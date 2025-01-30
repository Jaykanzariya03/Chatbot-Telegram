from pymongo import MongoClient
from config import MONGO_URI

client = MongoClient(MONGO_URI)
db = client["telegram_bot"]
users_collection = db["users_data"]
chat_history_collection = db["chat_history_data"]
files_collection = db["files_analyzed_data"]
search_history_collection = db["search_history_data"]
image_generation_collection = db["image_generation_data"]
voice_transcription_collection = db["voice_transcription_data"]
error_logs_collection = db["error_logs_data"]