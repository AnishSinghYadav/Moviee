import os
import openai
import requests
import logging
import telegram
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# Load API keys from .env
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OMDB_API_KEY = os.getenv("OMDB_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

# Initialize logging
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)

# Initialize OpenAI
openai.api_key = OPENAI_API_KEY

# Fetch movie details from OMDB API
def fetch_movie_details(movie_name):
    url = f"http://www.omdbapi.com/?t={movie_name}&apikey={OMDB_API_KEY}"
    response = requests.get(url)
    data = response.json()
    
    if data["Response"] == "False":
        return None
    
    return {
        "title": data.get("Title", "N/A"),
        "year": data.get("Year", "N/A"),
        "imdb_rating": data.get("imdbRating", "N/A"),
        "genre": data.get("Genre", "N/A"),
        "plot": data.get("Plot", "N/A"),
        "poster": data.get("Poster", ""),
    }

# Fetch YouTube trailer link
def fetch_youtube_trailer(movie_name):
    query = f"{movie_name} Official Trailer"
    url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q={query}&type=video&key={YOUTUBE_API_KEY}"
    
    response = requests.get(url)
    data = response.json()
    
    if "items" in data and len(data["items"]) > 0:
        video_id = data["items"][0]["id"]["videoId"]
        return f"https://www.youtube.com/watch?v={video_id}"
    
    return "Trailer not found."

# Fetch similar movie recommendations from OpenAI
def fetch_movie_recommendations(movie_name):
    prompt = f"Suggest 3 to 5 movies similar to '{movie_name}' and include their short description and IMDb rating."
    
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    
    return response["choices"][0]["message"]["content"].strip()

# Handle user messages
async def handle_message(update: Update, context: CallbackContext):
    movie_name = update.message.text
    chat_id = update.message.chat_id
    
    try:
        # Fetch movie details
        movie_details = fetch_movie_details(movie_name)
        if not movie_details:
            await update.message.reply_text("Movie not found! Please try another.")
            return
        
        # Fetch YouTube trailer
        trailer_link = fetch_youtube_trailer(movie_name)

        # Fetch similar movies
        similar_movies = fetch_movie_recommendations(movie_name)

        # Send movie details
        message = f"🎬 *{movie_details['title']}* ({movie_details['year']})\n"
        message += f"⭐ IMDb: {movie_details['imdb_rating']}\n"
        message += f"🎭 Genre: {movie_details['genre']}\n"
        message += f"📖 Plot: {movie_details['plot']}\n\n"
        message += f"🎥 [Watch Trailer]({trailer_link})\n\n"
        message += f"🎭 *Similar Movies:*\n{similar_movies}"

        await context.bot.send_photo(chat_id, photo=movie_details["poster"])
        await context.bot.send_message(chat_id, text=message, parse_mode=telegram.constants.ParseMode.MARKDOWN)
    
    except Exception as e:
        logging.error(f"Error fetching recommendation: {str(e)}")
        await update.message.reply_text("⚠️ Error fetching recommendation! Please try again.")

# Start bot
def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logging.info("Bot started successfully...")
    app.run_polling()

if __name__ == "__main__":
    main()
