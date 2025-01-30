from datetime import datetime, timezone
import os
from venv import logger
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from database import users_collection, chat_history_collection, files_collection, image_generation_collection, voice_transcription_collection, error_logs_collection
from ai import model1, model2, model3
from PIL import Image
import speech_recognition as sr
from pydub import AudioSegment


# Start Command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.message.from_user
        chat_id = update.message.chat_id

        # Check if user exists
        if users_collection.find_one({"chat_id": chat_id}):
            await update.message.reply_text("You are already registered! ✅")
        else:
            users_collection.insert_one({"first_name": user.first_name, "username": user.username, "chat_id": chat_id, "phone_number": None, "last_interaction": datetime.now(timezone.utc)})
            button = KeyboardButton("📞 Share Phone Number", request_contact=True)
            markup = ReplyKeyboardMarkup([[button]], resize_keyboard=True, one_time_keyboard=True)
            await update.message.reply_text("Click the button below to share your phone number.", reply_markup=markup)

    except Exception as e:
        logger.error(f"Error in start handler: {e}")
        error_logs_collection.insert_one({
            "chat_id": update.message.chat_id,
            "error_type": "Exception",
            "error_message": str(e),
            "timestamp": datetime.now(timezone.utc)
        })
        await update.message.reply_text("⚠️ Sorry, I encountered an error while processing your request.")


# Handle Contact Sharing
async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        contact = update.message.contact
        if contact:
            users_collection.update_one({"chat_id": update.message.chat_id}, {"$set": {"phone_number": contact.phone_number}})
            await update.message.reply_text("✅ Your phone number has been saved!")

    except Exception as e:
        logger.error(f"Error in handle_contact handler: {e}")
        error_logs_collection.insert_one({
            "chat_id": update.message.chat_id,
            "error_type": "Exception",
            "error_message": str(e),
            "timestamp": datetime.now(timezone.utc)
        })
        await update.message.reply_text("⚠️ Sorry, I encountered an error while saving your phone number.")


# AI Chat Handler
async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_message = update.message.text
        chat_id = update.message.chat_id

        response = model1.generate_content(user_message)
        ai_reply = response.text if response.text else "I'm not sure how to respond."

        # Store chat in database
        chat_history_collection.insert_one({"chat_id": chat_id, "user_message": user_message, "ai_response": ai_reply, "timestamp": datetime.now(timezone.utc)})
        
        await update.message.reply_text(ai_reply)

        users_collection.update_one(
            {"chat_id": chat_id},
            {"$set": {"last_interaction": datetime.now(timezone.utc)}},
            upsert=True
        )

    except Exception as e:
        logger.error(f"Error in chat handler: {e}")
        error_logs_collection.insert_one({
            "chat_id": update.message.chat_id,
            "error_type": "Exception",
            "error_message": str(e),
            "timestamp": datetime.now(timezone.utc)
        })
        await update.message.reply_text("⚠️ Sorry, I encountered an error while processing your message.")


# File Analysis Handler
async def analyze_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        file_name, file_path = None, None

        if update.message.document:  # If it's a file
            document = update.message.document
            file_name = document.file_name
            file_id = document.file_id

        elif update.message.photo:  # If it's an image
            photo = update.message.photo[-1]  # Get the highest resolution photo
            file_name = f"image_{update.message.message_id}.jpg"
            file_id = photo.file_id

        if file_id:
            new_file = await context.bot.get_file(file_id)
            file_path = f"./{file_name}"
            await new_file.download_to_drive(file_path)
            await update.message.reply_text("📂 Received! Analyzing the file...")

            # Analyze file/image with Gemini
            if file_name.lower().endswith((".jpg", ".png")):  # Image processing
                with Image.open(file_path) as image:
                    response = model2.generate_content(["Describe this image:", image]).text
            else:  # Other files (PDF, DOCX, etc.)
                response = model2.generate_content(f"Analyze this file: {file_name}").text

            # Send response
            await update.message.reply_text(f"📂 **File:** {file_name}\n📌 **Analysis:** {response}")

            # Save metadata in MongoDB
            files_collection.insert_one({
                "file_name": file_name,
                "description": response,
                "timestamp": datetime.now(timezone.utc)
            })

            # Clean up
            os.remove(file_path)  

    except Exception as e:
        logger.error(f"Error in analyze_file handler: {e}")
        error_logs_collection.insert_one({
            "chat_id": update.message.chat_id,
            "error_type": "Exception",
            "error_message": str(e),
            "timestamp": datetime.now(timezone.utc)
        })
        await update.message.reply_text("⚠️ Sorry, I encountered an error while analyzing the file.")


# Image Generation Handler
async def generate_image_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        chat_id = update.message.chat_id
        user_query = " ".join(context.args)  # Combine all arguments into a single query

        if not user_query:
            await update.message.reply_text("Please provide a query. Example: /generate futuristic cityscape")
            return

        # Generate the image using DALL·E
        await update.message.reply_text("Generating image... Please wait!")
        image_url = model3.generate_image(user_query)

        if image_url:
            # Send the generated image to the user
            await update.message.reply_photo(photo=image_url)

            # Store user query and generated image in the database
            image_generation_collection.insert_one({
                "chat_id": chat_id,
                "user_query": user_query,
                "image_url": image_url,
                "timestamp": datetime.now(timezone.utc)
            })
        else:
            await update.message.reply_text("Failed to generate image. Please try again later.")

    except Exception as e:
        logger.error(f"Error in generate_image_handler: {e}")
        error_logs_collection.insert_one({
            "chat_id": update.message.chat_id,
            "error_type": "Exception",
            "error_message": str(e),
            "timestamp": datetime.now(timezone.utc)
        })
        await update.message.reply_text("⚠️ Sorry, I encountered an error while generating the image.")


# Speech-to-Text Handler
async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        chat_id = update.message.chat_id

        # Get the voice message file
        voice_file = await update.message.voice.get_file()
        file_path = f"voice_message_{chat_id}.ogg"
        await voice_file.download_to_drive(file_path)

        # Convert OGG to WAV (optional, but SpeechRecognition works better with WAV)
        audio = AudioSegment.from_file(file_path, format="ogg")
        wav_path = f"voice_message_{chat_id}.wav"
        audio.export(wav_path, format="wav")

        # Initialize recognizer
        recognizer = sr.Recognizer()

        # Transcribe the audio
        with sr.AudioFile(wav_path) as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data)  

        # Send the transcribed text back to the user
        await update.message.reply_text(f"🎤 **Transcribed Text:**\n{text}")

        # Optionally, process the text further (e.g., send to Gemini chatbot)
        response = model1.generate_content(text)
        ai_reply = response.text if response.text else "I'm not sure how to respond."
        await update.message.reply_text(f"🤖 **AI Response:**\n{ai_reply}")

        voice_transcription_collection.insert_one({
            "chat_id": chat_id,
            "voice_file": file_path,
            "transcribed_text": text,
            "ai_response": ai_reply,
            "timestamp": datetime.now(timezone.utc)
        })

        # Clean up files
        os.remove(file_path)
        os.remove(wav_path)

        users_collection.update_one(
            {"chat_id": chat_id},
            {"$set": {"last_interaction": datetime.now(timezone.utc)}},
            upsert=True
        )

    except sr.UnknownValueError:
        await update.message.reply_text("⚠️ Sorry, I couldn't understand the audio.")
        error_logs_collection.insert_one({
            "chat_id": update.message.chat_id,
            "error_type": "UnknownValueError",
            "error_message": "Could not understand the audio.",
            "timestamp": datetime.now(timezone.utc)
        })
    except sr.RequestError as e:
        await update.message.reply_text(f"⚠️ Error: {e}")
        error_logs_collection.insert_one({
            "chat_id": update.message.chat_id,
            "error_type": "RequestError",
            "error_message": str(e),
            "timestamp": datetime.now(timezone.utc)
        })
    except Exception as e:
        logger.error(f"Error in handle_voice handler: {e}")
        error_logs_collection.insert_one({
            "chat_id": update.message.chat_id,
            "error_type": "Exception",
            "error_message": str(e),
            "timestamp": datetime.now(timezone.utc)
        })
        await update.message.reply_text("⚠️ Sorry, I encountered an error while processing your voice message.")