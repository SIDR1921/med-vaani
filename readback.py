from telegram import InlineKeyboardButton, InlineKeyboardMarkup
MISSING = "-not heard-"

def build_confirmation_text(records: list[dict],reminders_per_record: list[list[str]]) ->str:
    lines = ["Please check what I heard:*", ""]
    for i, (rec,reminders) in enumerate(zip(records,reminders_per_record),start=1):
        bp = MISSING
        if rec.get("systolic_bp") or rec.get("diastolic_bp"):
            bp = f"{rec.get('systolic_bp') or '?'} / {rec.get('diastolic_bp') or '?'}"
        lines.append(f"*{i}. {rec.get('patient_name')}*"
                     f"  ({rec.get('age') if rec.get('age') is not None else MISSING})"
                     f"  [BP: {bp}]")
        lines.append(f" BP: {bp}")
        lines.append(f"   Symptoms: {rec.get('symptoms') or MISSING}")

        if rec.get("village"):
            lines.append(f"   Village: {rec.get('village')}")
        
        for r in reminders:
            lines.append(f"   ⚠️ {r}")
        lines.append("")

    lines.append("If any of the above is incorrect, please correct it before submission.")
    return "\n".join(lines)


def build_confirmation_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Confirm", callback_data="confirm")],
            [InlineKeyboardButton("Edit", callback_data="edit")]
        ]
    )


