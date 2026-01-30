# MedVaani: Offline-First Voice Assistant for Healthcare

MedVaani is an AI-powered field assistant that automates data entry for  Health Activist workers in rural India. Users can record patient data via voice notes . The system transcribes, extracts, and stores structured data in a local database—no internet required for processing.

---

## System Overview

**Key Features:**
- Offline-first: All AI runs locally for privacy and zero data cost.
- Multilingual: Transcribes and translates voice notes to English records.
- Batch mode: Process multiple patients in a single voice note.
- Structured output: Converts unstructured speech to a normalized SQL database.

---


---

## Technology Stack
- Python 3.10+
- Meta Llama 3.2 (via Ollama)
- OpenAI Whisper (small/medium)
- SQLite
- python-telegram-bot
- FastAPI (for future API/webhook extension)

---

## Quickstart

### Prerequisites
- Python 3.10 or higher
- Ollama installed and running
- FFmpeg (for audio processing)

### Setup
1. **Clone the repository:**
   ```sh
   git clone <your-repo-url>
   cd asha_bot
   ```
2. **Create and activate a virtual environment:**
   ```sh
   python3 -m venv venv
   source venv/bin/activate
   ```
3. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```
4. **Install FFmpeg:**
   - macOS: `brew install ffmpeg`
   - Ubuntu: `sudo apt-get install ffmpeg`
5. **Start Ollama and pull the Llama 3.2 model:**
   ```sh
   ollama serve
   ollama pull llama3.2
   ```
6. **Set your Telegram Bot Token:**
   - Create a `.env` file in `asha_bot` with:
     ```
     TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
     ```
   - **Important:** Do NOT commit your `.env` file or any file containing secrets to version control (e.g., GitHub). Add `.env` to your `.gitignore` file.
7. **Run the bot:**
   ```sh
   python main.py
   ```

---

## Usage
- Send a voice note to your Telegram bot .
- The bot transcribes, extracts, and stores patient data locally.
- Batch mode: Mention multiple patients in one note (e.g., "First patient is... Second patient is...").
- The bot replies with a structured field report and saves all records to SQLite.

---

## Notes
- All AI processing is local; no data leaves your device.
- For best results, speak clearly and mention patient details in a structured way.
- The system is extensible for more languages and future API/webhook integrations.

---

