from collections import Counter
from datetime import datetime, timedelta, timezone
from venv import logger
from telegram import Update
from telegram.ext import ContextTypes
from database import users_collection, chat_history_collection, files_collection,search_history_collection,image_generation_collection,voice_transcription_collection,error_logs_collection

# Admin Analytics Dashboard Handler
async def admin_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id

    # Check if the user is an admin (you can define a list of admin chat IDs)
    admins = [7347901625]  # Replace with your admin chat IDs
    if chat_id not in admins:
        await update.message.reply_text("🚫 You are not authorized to access this feature.")
        return

    try:
        # Fetch analytics data from MongoDB
        total_users = users_collection.count_documents({})

        active_users = users_collection.count_documents({"last_interaction": {"$gte": datetime.now(timezone.utc) - timedelta(days=7)}})

        total_chats = chat_history_collection.count_documents({})
        total_files_analyzed = files_collection.count_documents({})
        total_searches = search_history_collection.count_documents({})
        total_images_generated = image_generation_collection.count_documents({})
        total_voice_transcriptions = voice_transcription_collection.count_documents({})


        # Format the analytics data
        analytics_message = (
            f"📊 **Admin Dashboard**\n\n"
            f"👥 Total Users : {total_users}\n"
            f"🚀 Active Users (Last 7 Days) : {active_users}\n\n"
        )

        analytics_message += f"\n💬 Total Chats : {total_chats}\n"

        analytics_message += f"📂 Files Analyzed : {total_files_analyzed}\n"

        # Add web search statistics
        analytics_message += f"🔍 Web Searches : {total_searches}\n"

        # Add image generation statistics
        analytics_message += f"🎨 Images Generated : {total_images_generated}\n"

        # Add voice transcription statistics
        analytics_message += f"🎤 Voice Transcriptions : {total_voice_transcriptions}\n"


        total_errors = error_logs_collection.count_documents({})

        analytics_message += f"\n⚠️ Total Errors : {total_errors}"

        # Send the analytics message to the admin
        await update.message.reply_text(analytics_message)



      
    except Exception as e:
        logger.error(f"Error in admin dashboard: {e}")
        await update.message.reply_text("⚠️ Sorry, I encountered an error while generating the analytics dashboard.")