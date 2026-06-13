import os
import logging
import asyncio
import urllib.request
import json
from http.server import SimpleHTTPRequestHandler, HTTPServer
from threading import Thread
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

# 1. Enable Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ==========================================
# CONFIGURATION
# ==========================================
BOT_TOKEN = "8747299464:AAESNSeAMaCJAFD-jIuNQeyZp2dJDMausO0"  
CHANNEL_ID = "-1002375727016"  

# ==========================================
# FULL LYRICS FETCHING FUNCTION (Web API)
# ==========================================
def fetch_full_lyrics(song_title):
    """
    Searches a public API to get the absolute full lyrics dynamically.
    """
    try:
        # Clean the input query for the API URL
        query = urllib.parse.quote(f"Forrest Frank {song_title}")
        url = f"https://api.lyrics.ovh/v1/Forrest%20Frank/{urllib.parse.quote(song_title)}"
        
        # Request lyrics safely
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            if "lyrics" in data and data["lyrics"].strip():
                return data["lyrics"]
    except Exception as e:
        logger.error(f"Error fetching from primary lyrics API: {e}")
    
    # Fallback backup message if the API fails or doesn't have the collab yet
    return None

# ==========================================
# TELEGRAM BOT HANDLERS
# ==========================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "👋 Welcome to the Ultimate Forrest Frank Hub Bot!\n\n"
        "I can give you the COMPLETE lyrics to any Forrest Frank song or collaboration.\n\n"
        "🎵 **How to use:**\n"
        "Type `/lyrics <song name>`\n"
        "Example: `/lyrics good day` or `/lyrics altar`"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

async def get_lyrics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Please specify a song name.\nExample: `/lyrics up!`", parse_mode="Markdown")
        return
        
    song_query = " ".join(context.args).strip()
    await update.message.reply_text(f"🔍 Searching for the complete lyrics to *'{song_query}'*...", parse_mode="Markdown")
    
    # Get complete lyrics dynamically
    full_lyrics = fetch_full_lyrics(song_query)
    
    if full_lyrics:
        # Prevent Telegram message character limits from breaking the bot
        if len(full_lyrics) > 4000:
            full_lyrics = full_lyrics[:3900] + "\n\n...(Lyrics truncated due to length)"
            
        response_text = f"🎶 **Complete Lyrics for '{song_query.title()}' by Forrest Frank:**\n\n{full_lyrics}"
    else:
        # Beautiful failure message showing his complete main list if typing was wrong
        response_text = (
            f"⚠️ Could not automatically extract the text for '{song_query.title()}'.\n\n"
            "💡 Make sure you spelled it correctly! Try searching popular ones like:\n"
            "• Good Day\n• Up! (feat. Connor Price)\n• Altar (feat. Hulvey)\n"
            "• No Longer Bound\n• Never Get Used To This (feat. JVKE)\n• Thankful\n• Lemonade"
        )
        
    await update.message.reply_text(response_text)

async def handle_audio_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.audio:
        audio_file_id = update.message.audio.file_id
        caption = update.message.caption or f"🎵 {update.message.audio.title or 'Forrest Frank Track'}"
        try:
            await context.bot.send_audio(
                chat_id=CHANNEL_ID,
                audio=audio_file_id,
                caption=f"{caption}\n\n📢 Shared via @ForrestFrank Hub"
            )
            await update.message.reply_text("🚀 Track successfully deployed and posted to your channel!")
        except Exception as e:
            await update.message.reply_text(f"❌ Failed to forward to channel. Error: {e}")

# ==========================================
# RENDER KEEP-ALIVE WEB ENGINE
# ==========================================
class HealthCheckHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"Forrest Frank Engine Online!")

def run_health_server():
    server = HTTPServer(("0.0.0.0", 8080), HealthCheckHandler)
    server.serve_forever()

# ==========================================
# MAIN APPLICATON STARTUP
# ==========================================
def main():
    server_thread = Thread(target=run_health_server)
    server_thread.daemon = True
    server_thread.start()

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("lyrics", get_lyrics))
    app.add_handler(MessageHandler(filters.AUDIO, handle_audio_upload))

    print("Bot is starting up...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
