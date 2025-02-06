import os
import openai
import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# Load environment variables
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OMDB_API_KEY = os.getenv("OMDB_API_KEY")

# Set OpenAI API key
openai.api_key = OPENAI_API_KEY  # ✅ Correct for openai<=0.28

async def start(update: Update, context: CallbackContext):
    """Send a welcome message when the bot starts"""
    await update.message.reply_text("🎬 Welcome to the Movie Bot! Send me a movie name to get recommendations.")

async def get_movie_recommendation(update: Update, context: CallbackContext):
    """Fetch movie recommendations from OpenAI and show posters from OMDB"""
    user_movie = update.message.text.strip()

    # Step 1: Inform the user that recommendations are being fetched
    await update.message.reply_text(f"🔍 Searching for movies similar to *{user_movie}*...", parse_mode="Markdown")

    # Step 2: Get movie recommendations from OpenAI
    prompt = (
        f"Recommend five movies similar to '{user_movie}'. "
        "For each movie, provide the following details in this exact format:\n\n"
        "Movie Name: <name>\n"
        "Description: <brief description>\n"
        "Rating: <rating out of 10>\n"
        "Release Year: <year>\n"
        "Top 3 Cast Members: <actor 1>, <actor 2>, <actor 3>\n\n"
    )

    try:
        response = openai.ChatCompletion.create(  # ✅ Correct for openai==0.28
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        movie_data = response["choices"][0]["message"]["content"]

        # Step 3: Split the response into different movies
        movie_entries = movie_data.strip().split("\n\n")  # Each movie block is separated by a double newline
        movies = []

        for entry in movie_entries:
            lines = entry.split("\n")
            if len(lines) >= 5:
                movie_info = {
                    "name": lines[0].split(":")[1].strip(),
                    "description": lines[1].split(":")[1].strip(),
                    "rating": lines[2].split(":")[1].strip(),
                    "year": lines[3].split(":")[1].strip(),
                    "cast": lines[4].split(":")[1].strip()
                }
                movies.append(movie_info)

        # Step 4: Fetch posters from OMDB API
        posters = {}
        for movie in movies:
            omdb_url = f"http://www.omdbapi.com/?t={movie['name']}&apikey={OMDB_API_KEY}"
            omdb_response = requests.get(omdb_url).json()
            posters[movie['name']] = omdb_response.get("Poster", None)  # None if poster not found

        # Step 5: Send response to Telegram
        reply_text = f"🎬 *You searched for:* {user_movie}\n\n"
        reply_text += "Here are 5 similar movies:\n\n"

        for movie in movies:
            reply_text += (
                f"🎥 *{movie['name']}*\n"
                f"📖 *Description:* {movie['description']}\n"
                f"⭐ *Rating:* {movie['rating']}/10\n"
                f"📅 *Release Year:* {movie['year']}\n"
                f"🎭 *Top Cast:* {movie['cast']}\n\n"
            )

        await update.message.reply_text(reply_text, parse_mode="Markdown")

        # Step 6: Send posters one by one
        for movie in movies:
            poster_url = posters.get(movie['name'])
            if poster_url:
                await update.message.reply_photo(photo=poster_url, caption=f"🎬 *{movie['name']}*", parse_mode="Markdown")

    except Exception as e:
        await update.message.reply_text(f"⚠️ Error fetching recommendation: {str(e)}")

async def error_handler(update: Update, context: CallbackContext):
    """Handle errors"""
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
