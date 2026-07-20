import os 
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

_raw_ids = os.getenv("ALLOWED_USER_IDS", "")
ALLOWED_USER_IDS = {int(x) for x in _raw_ids.split(",") if x.strip().isdigit()}

WHISPER_MODEL = os.getenv("WHISPER_MODEL", "small")
WHISPER_LANGUAGE = os.getenv("WHISPER_LANGUAGE") or None
LLM_MODEL = os.getenv("LLM_MODEL", "llama3.2")

DB_PATH = os.getenv("DB_PATH" , "medvaani.db")
RETENTION_DAYS = int(os.getenv("RETENTION_DAYS", "365"))

VALID_RANGES = {
    "age" : (0,120),
    "systolic_bp" : (60,260),
    "diastolic_bp" : (30,160),
}