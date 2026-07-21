import logging

from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

from telegram.request import HTTPXRequest

import bot
import config
import db
from asr import WhisperEngine

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

def main():
    db.init_db()
    conn = db.get_conn()
    purged = db.purge_expired(conn)
    if purged:
        logging.info("Retention policy: purged %d expired visits", purged)

    bot.asr_engine = WhisperEngine(config.WHISPER_MODEL, config.WHISPER_LANGUAGE)

    request = HTTPXRequest(
        connection_pool_size=8, read_timeout=60,
        write_timeout=20.0, connect_timeout=20.0,
    )
    app = ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN).request(request).build()

    app.add_handler(CommandHandler("start", bot.start))
    app.add_handler(MessageHandler(filters.VOICE, bot.handle_voice))
    app.add_handler(CallbackQueryHandler(bot.handle_confirmation, pattern="^(confirm|discard)$"))
    logging.info("Medvaani is now online!")
    app.run_polling()

if __name__ == "__main__":
    main()