import asyncio
import logging
import os
from telegram import Update
from telegram.ext import ContextTypes

import db
import matcher
import readback
import risk
from extractor import extract_patient 
from security import allowlisted
from segmenter import segment_transcript

logger = logging.getLogger(__name__)
asr_engine = None

@allowlisted
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Namaste! I am MedVaani. Send me a voice report about your patient visits."
    )

@allowlisted
async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎧 Processing your report...")

    voice_file = await context.bot.get_file(update.message.voice.file_id)
    audio_path = f"voice_{update.message.voice.file_unique_id}.ogg"
    await voice_file.download_to_drive(audio_path)

    try:
        loop = asyncio.get_running_loop()
        transcript = await loop.run_in_executor(None, asr_engine.transcribe, audio_path)
        logger.info("Transcript length: %d chars", len(transcript))

        segments = await loop.run_in_executor(None, segment_transcript, transcript)

        records = []
        for seg in segments:
            rec = await loop.run_in_executor(None, extract_patient, seg)
            if rec:
                records.append(rec)

        if not records:
            await update.message.reply_text(
                "I could not hear any patient details. Please re-record, "
                "mentioning the name first."
            )
            return

        reminders_per_record = [risk.protocol_reminders(rec) for rec in records]

        # Hold in memory; save only after the worker confirms.
        context.user_data["pending_records"] = records
        context.user_data["pending_reminders"] = reminders_per_record

        await update.message.reply_text(
            readback.build_confirmation_text(records, reminders_per_record),
            parse_mode="Markdown",
            reply_markup=readback.build_confirmation_keyboard(),
        )

    except Exception:
        logger.exception("Voice processing failed")
        await update.message.reply_text("Something went wrong. Please try again.")
    finally:
        if os.path.exists(audio_path):
            os.remove(audio_path)


@allowlisted
async def handle_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()  # stop the button's loading spinner

    records = context.user_data.pop("pending_records", None)
    reminders = context.user_data.pop("pending_reminders", [])
    user_id = update.effective_user.id

    if query.data == "discard" or not records:
        await query.edit_message_text("🗑Discarded. Send a new voice note when ready.")
        return

    conn = db.get_conn()
    try:
        saved = 0
        for rec, recs_reminders in zip(records, reminders):
            existing = matcher.find_candidate(
                conn, rec["patient_name"], rec.get("age"), rec.get("village")
            )
            if existing:
                patient_id = existing["id"]
            else:
                patient_id = db.create_patient(
                    conn,
                    rec["patient_name"],
                    matcher.normalize_name(rec["patient_name"]),
                    rec.get("age"),
                    rec.get("village"),
                )
            visit_id = db.save_visit(conn, patient_id, rec, recs_reminders, user_id)
            db.record_consent(conn, patient_id, visit_id, attested_by=user_id)
            saved += 1

        db.log_action(conn, user_id, "save_visits", f"count={saved}")
        conn.commit()
        await query.edit_message_text(f"Saved {saved} record(s). Dhanyavaad!")
    except Exception:
        conn.rollback()
        logger.exception("Save failed")
        await query.edit_message_text("Could not save. Nothing was recorded — try again.")
    finally:
        conn.close()