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
openai.api_key = OPENAI_API_KEY

async def start(update: Update, context: CallbackContext):
    """Send a welcome message when the bot starts"""
    await update.message.reply_text("🎬 Welcome to the Movie Bot! Send me a movie name to get recommendations.")

async def get_movie_recommendation(update: Update, context: CallbackContext):
    """Fetch movie recommendations from OpenAI and show posters from OMDB"""
    user_message = update.message.text.strip()

    # Step 1: Get movie recommendation from OpenAI
    prompt = f"Recommend a movie similar to {user_message} and provide its name, description, rating, release date, and top 3 cast members."
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        movie_data = response["choices"][0]["message"]["content"]

        # Step 2: Extract movie name for OMDB API
        movie_lines = movie_data.split("\n")
        movie_name = movie_lines[0].split(":")[-1].strip()  # Extract the first line as the movie name
        
        # Step 3: Fetch movie poster from OMDB API
        omdb_url = f"http://www.omdbapi.com/?t={movie_name}&apikey={OMDB_API_KEY}"
        omdb_response = requests.get(omdb_url).json()
        poster_url = omdb_response.get("Poster", "No poster available")

        # Step 4: Send response to Telegram
        reply_text = f"🎬 *Movie Recommendation:*\n{movie_data}"
        await update.message.reply_photo(photo=poster_url, caption=reply_text, parse_mode="Markdown")

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
