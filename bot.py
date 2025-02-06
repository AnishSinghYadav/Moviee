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
        "For each movie, provide its name, description, rating, release year, and top 3 cast members."
    )
    
    try:
        response = openai.ChatCompletion.create(  # ✅ Correct for openai==0.28
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        movie_data = response["choices"][0]["message"]["content"]
        movie_lines = movie_data.split("\n")

        # Step 3: Extract five movie names
        recommended_movies = []
        for line in movie_lines:
            if line.strip().startswith("1.") or line.strip().startswith("2.") or \
               line.strip().startswith("3.") or line.strip().startswith("4.") or \
               line.strip().startswith("5."):
                recommended_movies.append(line.split(".")[-1].strip())

        # Step 4: Fetch posters from OMDB API
        posters = {}
        for movie in recommended_movies:
            omdb_url = f"http://www.omdbapi.com/?t={movie}&apikey={OMDB_API_KEY}"
            omdb_response = requests.get(omdb_url).json()
            posters[movie] = omdb_response.get("Poster", None)  # None if poster not found

        # Step 5: Send response to Telegram
        reply_text = f"🎬 *You searched for:* {user_movie}\n\n"
        reply_text += "Here are 5 similar movies:\n\n"

        for i, movie in enumerate(recommended_movies, start=1):
            reply_text += f"🎥 *{i}. {movie}*\n"

        await update.message.reply_text(reply_text, parse_mode="Markdown")

        # Send movie posters one by one
        for movie, poster in posters.items():
            if poster:
                await update.message.reply_photo(photo=poster, caption=f"🎬 *{movie}*", parse_mode="Markdown")

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
