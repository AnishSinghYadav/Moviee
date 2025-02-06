import os
import openai
import requests
import re
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# Load environment variables
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OMDB_API_KEY = os.getenv("OMDB_API_KEY")

# Set OpenAI API Key
openai.api_key = OPENAI_API_KEY

async def start(update: Update, context: CallbackContext):
    """Start the bot with a welcome message."""
    await update.message.reply_text("🎬 Welcome to the Movie Bot! Send me a movie name to get recommendations.")

async def get_movie_recommendation(update: Update, context: CallbackContext):
    """Fetch movie recommendations from OpenAI and show posters from OMDB."""
    user_movie = update.message.text.strip()

    await update.message.reply_text(f"🔍 Searching for movies similar to *{user_movie}*...", parse_mode="Markdown")

    # Step 1: Get movie recommendations from OpenAI
    prompt = (
        f"Recommend five movies similar to '{user_movie}'. "
        "For each movie, provide details in this exact format:\n\n"
        "**Movie Name:** <movie name>\n"
        "**Description:** <brief description>\n"
        "**Rating:** <rating out of 10>\n"
        "**Release Year:** <year>\n"
        "**Top 3 Cast Members:** <actor 1>, <actor 2>, <actor 3>\n\n"
        "Make sure each movie entry follows this format exactly."
    )

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        movie_data = response["choices"][0]["message"]["content"]

        # Step 2: Extract structured movie details using regex
        movie_pattern = re.compile(
            r"\*\*Movie Name:\*\* (.*?)\n"
            r"\*\*Description:\*\* (.*?)\n"
            r"\*\*Rating:\*\* (.*?)\n"
            r"\*\*Release Year:\*\* (.*?)\n"
            r"\*\*Top 3 Cast Members:\*\* (.*?)\n",
            re.DOTALL
        )
        
        movies = movie_pattern.findall(movie_data)
        movie_list = []

        for movie in movies:
            movie_info = {
                "name": movie[0].strip(),
                "description": movie[1].strip(),
                "rating": movie[2].strip(),
                "year": movie[3].strip(),
                "cast": movie[4].strip()
            }
            movie_list.append(movie_info)

        # Step 3: Fetch posters from OMDB API
        posters = {}
        for movie in movie_list:
            omdb_url = f"http://www.omdbapi.com/?t={movie['name']}&apikey={OMDB_API_KEY}"
            omdb_response = requests.get(omdb_url).json()
            posters[movie['name']] = omdb_response.get("Poster", None)  # None if poster not found

        # Step 4: Send text details first
        reply_text = f"🎬 *You searched for:* {user_movie}\n\n"
        reply_text += "Here are 5 similar movies:\n\n"

        for movie in movie_list:
            reply_text += (
                f"🎥 *{movie['name']}*\n"
                f"📖 *Description:* {movie['description']}\n"
                f"⭐ *Rating:* {movie['rating']}/10\n"
                f"📅 *Release Year:* {movie['year']}\n"
                f"🎭 *Top Cast:* {movie['cast']}\n\n"
            )

        await update.message.reply_text(reply_text, parse_mode="Markdown")

        # Step 5: Send posters one by one
        for movie in movie_list:
            poster_url = posters.get(movie['name'])
            if poster_url:
                await update.message.reply_photo(photo=poster_url, caption=f"🎬 *{movie['name']}*", parse_mode="Markdown")

    except Exception as e:
        await update.message.reply_text(f"⚠️ Error fetching recommendation: {str(e)}")

async def error_handler(update: Update, context: CallbackContext):
    """Handle errors."""
    print(f"Error: {context.error}")

# Initialize bot application
app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

# Add handlers
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, get_movie_recommendation))
app.add_error_handler(error_handler)

# Start the bot
print("🤖 Bot is running...")
app.run_polling()
