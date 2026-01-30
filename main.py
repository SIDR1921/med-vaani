import os
import logging
import json
import asyncio
import re
import sqlite3
from datetime import datetime

import ollama
import whisper
from dotenv import load_dotenv

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from telegram.request import HTTPXRequest

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")




print("⏳ Loading Whisper Model (The Ears)...")
ear_model = whisper.load_model("small")
print("Whisper Loaded!")

DB_NAME = "asha_records.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            age INTEGER,
            systolic INTEGER,
            diastolic INTEGER,
            symptoms TEXT,
            risk_status TEXT,
            timestamp DATETIME
        )
    ''')
    conn.commit()
    conn.close()
def save_patient(name, age, sys, dia, symptoms, risk):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        INSERT INTO patients (name, age, systolic, diastolic, symptoms, risk_status, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (name, age, sys, dia, symptoms, risk, datetime.now()))
    conn.commit()
    conn.close()


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


def transcribe_audio_locally(audio_path):
    print(f"👂 Listening to {audio_path}...")
    result = ear_model.transcribe(audio_path)
    text = result["text"]
    print(f"📝 Transcribed: {text}")
    return text


def analyze_batch_with_llama(text_data):
    print("🧠 Thinking (Splitting Text & Analyzing)...")
    
    # 1. Python Logic: Split text into chunks based on common keywords
    # This helps the small model focus on one person at a time.
    # We split by "First", "Second", "Third", "Fourth", "Next", or "Patient"
    import re
    # This regex looks for sentence starts indicating a new person
    # It matches "First", "Second", "Next", "Another", etc.
    chunks = re.split(r'(?i)(?=\b(First|Second|Third|Fourth|Fifth|Next|Another)\b)', text_data)
    
    # Remove empty chunks
    chunks = [c.strip() for c in chunks if len(c.strip()) > 10]
    
    all_patients = []
    
    # 2. Loop through each chunk and ask Llama to extract ONE person
    for chunk in chunks:
        print(f"   🔍 Analyzing chunk: {chunk[:30]}...")
        
        prompt = f"""
        Extract the medical data for the patient described in this text.
        
        Text: "{chunk}"
        
        Required JSON:
        {{
            "patient_name": "String",
            "age": Integer or null,
            "systolic_bp": Integer or null,
            "diastolic_bp": Integer or null,
            "symptoms": "String"
        }}
        
        Rules:
        - Return ONLY the JSON object.
        - If no patient data is found in this chunk, return null.
        """
        
        try:
            response = ollama.chat(
                model='llama3.2', 
                messages=[{'role': 'user', 'content': prompt}],
                format='json'
            )
            
            content = response['message']['content']
            data = json.loads(content)
            
            # Only add if we actually found a name
            if data and data.get('patient_name'):
                all_patients.append(data)
                
        except Exception as e:
            print(f"   ⚠️ Llama skipped a chunk: {e}")
            continue

    # 3. Convert the list back to a JSON string for the main code to use
    return json.dumps(all_patients)

def clean_json_response(text_response):
    """Sanitizes the Llama output to get pure JSON"""
    cleaned = re.sub(r"```json\s*|\s*```", "", text_response)
    start = cleaned.find('{')
    end = cleaned.rfind('}') + 1
    if start != -1 and end != 0:
        cleaned = cleaned[start:end]
    return cleaned


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Namaste! I am MedVaani (Running Locally). Send me a voice report.")

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    await update.message.reply_text(f" Processing ...")

    voice = update.message.voice
    file_id = voice.file_id
    file_path = f"voice_{file_id}.ogg"

    
    new_file = await context.bot.get_file(file_id)
    await new_file.download_to_drive(file_path)

    try:
        loop = asyncio.get_running_loop()
        transcribed_text = await loop.run_in_executor(None, transcribe_audio_locally, file_path)
        
        json_response = await loop.run_in_executor(None, analyze_batch_with_llama, transcribed_text)
        
        patients = json.loads(json_response)
        
        if isinstance(patients, dict):
            patients = [patients]

        saved_count = 0
        report_msg = f"📝 **Field Report**\n_Input: {transcribed_text}_\n\n"

        for p in patients:
            name = p.get('patient_name', 'Unknown')
            age = p.get('age')
            sys = p.get('systolic_bp')
            dia = p.get('diastolic_bp')
            symptoms = p.get('symptoms', 'None')

            # Risk Logic
            if isinstance(sys, int) and sys > 140:
                status = "⚠️ **HIGH RISK**"
            else:
                status = "✅ Normal"

            # Save to Database
            save_patient(name, age, sys, dia, symptoms, status)
            saved_count += 1

            # Add to reply message
            report_msg += (
                f"👤 **{name}** ({age or 'Age N/A'})\n"
                f"❤️ BP: {sys}/{dia} | {status}\n"
                f"🤒 {symptoms}\n"
                f"-------------------\n"
            )

        report_msg += f"\n💾 **Saved {saved_count} records to Database.**"
        await update.message.reply_text(report_msg, parse_mode='Markdown')

    except Exception as e:
        logging.error(f"Error: {e}")
        await update.message.reply_text("❌ Error. Please speak clearly and try again.")
        
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)


if __name__ == '__main__':
    init_db()
    t_request = HTTPXRequest(connection_pool_size=8, read_timeout=60, write_timeout=20.0, connect_timeout=20.0)

    app = ApplicationBuilder().token(TOKEN).request(t_request).build()

    app.add_handler(CommandHandler('start', start))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))

    print("MedVaani is Online!")
    app.run_polling()