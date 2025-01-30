import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SERPAPI_KEY = os.getenv("SERPAPI_KEY")
NGROK_AUTH_TOKEN = os.getenv("NGROK_AUTH_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
