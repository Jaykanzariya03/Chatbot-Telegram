from telegram import Update
from telegram.ext import ContextTypes
from serpapi import GoogleSearch
from ai import model2
from database import search_history_collection
from config import SERPAPI_KEY
import datetime

async def web_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args)
    chat_id = update.message.chat_id

    if not query:
        await update.message.reply_text("🔍 Please provide a search query. Example: `/websearch latest AI news`")
        return

    await update.message.reply_text("🌍 Searching the web... Please wait.")

    try:
        params = {"q": query, "api_key": SERPAPI_KEY}
        search_results = GoogleSearch(params).get_dict()

        if search_results and "organic_results" in search_results:
            top_links = "\n".join([f"🔗 {result['title']}: {result['link']}" for result in search_results['organic_results'][:5]])
            summary_response = model2.generate_content(f"Summarize these search results:\n{top_links}")
            summary_text = summary_response.text if summary_response.text else "No summary available."

            search_history_collection.insert_one({"chat_id": chat_id, "query": query, "summary": summary_text, "top_links": search_results['organic_results'][:5], "timestamp": datetime.datetime.utcnow()})

            await update.message.reply_text(f"🔎 **Results for:** `{query}`\n\n📌 **Summary:**\n{summary_text}\n\n🌐 **Links:**\n{top_links}")
        else:
            await update.message.reply_text("❌ No results found.")

    except Exception as e:
        print(f"Error in web search: {e}")
        await update.message.reply_text("⚠️ Error occurred during web search.")
