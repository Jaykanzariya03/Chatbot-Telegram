import logging
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from handlers import start, handle_contact, chat, analyze_file, generate_image_handler, handle_voice
from dashboard import admin_dashboard
from search import web_search
from config import BOT_TOKEN

# Enable logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize bot
application = ApplicationBuilder().token(BOT_TOKEN).build()

# Add handlers
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.CONTACT, handle_contact))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
application.add_handler(MessageHandler(filters.Document.ALL | filters.PHOTO, analyze_file))
application.add_handler(CommandHandler("websearch", web_search))
application.add_handler(CommandHandler("generate", generate_image_handler))
application.add_handler(MessageHandler(filters.VOICE, handle_voice))
application.add_handler(CommandHandler("dashboard", admin_dashboard))

# Run bot
if __name__ == "__main__":
    print("🚀 Bot is running...")
    application.run_polling()
