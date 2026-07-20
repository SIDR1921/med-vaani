import functools
import logging
import config

logger = logging.getLogger(__name__)

def allowlisted(handler):
    """Only let users in config.ALLOWED_USER_IDS reach the wrapped handler."""
    @functools.wraps(handler)
    async def wrapper(update,context):
        user = update.effective_user
        if user is None or user.id not in config.ALLOWED_USER_IDS:
            uid = user.id if user else "unknown"
            logger.warning("Rejected message from unauthorised user %s", uid)
            
            if update.effective_message:
                await update.effective_message.reply_text("Sorry, this bot is restricted to registered health workers.")
                return
            return await handler(update,context)
        
    return wrapper
