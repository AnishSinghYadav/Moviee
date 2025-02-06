import os
import openai
import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Load API keys from .env file
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OMDB_API_KEY = os.getenv("OMDB_API_KEY")

openai.api_key = OPENAI_API_KEY

# Function to fetch movie recommendations using OpenAI
def get_movie_recommendation(movie_name):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": f"Recommend a movie like {movie_name} and provide its description, rating, release date, and top 3 cast members."}]
        )
        return response["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"Error in OpenAI API: {e}")
        return None

# Function to get movie poster from OMDB API
def get_movie_poster(movie_name):
    url = f"http://www.omdbapi.com/?t={movie_name}&apikey={OMDB_API_KEY}"
    response = requests.get(url).json()
    
    if "Poster" in response:
        return response["Poster"]
    return None

# Handle movie request from Telegram users
def handle_movie_request(update: Update, context: CallbackContext):
    movie_name = update.message.text
    update.message.reply_text(f"🔍 Searching for recommendations for '{movie_name}'...")

    recommendation = get_movie_recommendation(movie_name)
    poster_url = get_movie_poster(movie_name)

    if recommendation:
        message = f"🎬 *{movie_name}*\n\n{recommendation}\n\n"
        if poster_url:
            update.message.reply_text(message, parse_mode="Markdown")
            update.message.reply_photo(photo=poster_url)
        else:
            update.message.reply_text(message, parse_mode="Markdown")
    else:
        update.message.reply_text("❌ Error fetching recommendation. Please try again later.")

# Start Telegram bot
def main():
    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_movie_request))
    
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
