import os
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
import time
import re
import urllib.parse
import requests
import telebot
from telebot import types

# ==========================================
# CORE CONFIGURATION
# ==========================================
BOT_TOKEN = "8747299464:AAFqYZTvm0Sh8tFDOcqj8UioBcrtnO2P4y8"
CHANNEL_ID = "-1002375727016" 

bot = telebot.TeleBot(BOT_TOKEN, threaded=True)

# ==========================================
# DYNAMIC LAYOUT KEYBOARD MENU
# ==========================================
def get_main_menu_keyboard():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = types.KeyboardButton("☀️ Good Day")
    btn2 = types.KeyboardButton("⚓ No Longer Bound")
    btn3 = types.KeyboardButton("🔥 Never Walk Alone")
    btn4 = types.KeyboardButton("🤍 Always")
    btn5 = types.KeyboardButton("✨ Search Any Artist / Song")
    markup.add(btn1, btn2, btn3, btn4, btn5)
    return markup

# ==========================================
# PUBLIC PARSING SEARCH ENGINE (NO TOKENS)
# ==========================================
def fetch_any_lyrics(search_query):
    """Queries public lyric structures directly via web request engines without requiring API access tokens."""
    try:
        # Standardize formatting for universal search indexing
        clean_query = search_query.replace("☀️ ", "").replace("⚓ ", "").replace("🔥 ", "").replace("🤍 ", "")
        
        # Format a clean string to pull from an open, unauthenticated lyrics index
        url = f"https://api.lyrics.ovh/v1/search?q={urllib.parse.quote(clean_query)}"
        
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            # If the open repository returns valid matching tracks
            if data.get("data"):
                top_track = data["data"][0]
                title = top_track.get("title", "Unknown Track")
                artist = top_track.get("artist", {}).get("name", "Unknown Artist")
                preview = top_track.get("preview", "")
                
                # Secondary deep-fetch for full lyric lines block
                lyrics_url = f"https://api.lyrics.ovh/v1/{artist}/{title}"
                lyrics_resp = requests.get(lyrics_url, timeout=8)
                
                if lyrics_resp.status_code == 200:
                    lyrics_text = lyrics_resp.json().get("lyrics", "").strip()
                    if lyrics_text:
                        return f"🎵 **LYRICS: {title.upper()}** 🎵\nBy {artist}\n\n{lyrics_text}"
                
                # Fallback layout if full text is blocked but song exists
                if preview:
                    return f"🎵 **TRACK FOUND: {title}** by {artist}\n\nThe full text block is restricted, but you can listen to an audio preview snippet right here:\n👉 {preview}"
                    
        return f"❌ System couldn't extract text matching '{clean_query}'. Try typing the Artist Name + Song Title together for better accuracy!"
    except Exception as e:
        print(f"[ENGINE ERROR] {e}")
        return "⚠️ The public database is currently refreshing. Please try sending your song search again in a few seconds!"

# ==========================================
# TELEGRAM BOT LOGIC HANDLERS
# ==========================================
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    try:
        welcome_text = (
            f"👋 *Welcome to the Global Lyrics Search Bot!*\n\n"
            f"Powered by an open, token-free database network. You can search for **ANY artist or song** globally!\n\n"
            f"👉 **How to use me:**\n"
            f"• Tap any quick-access button below.\n"
            f"• Or simply **type any artist and song name** directly into the chat box (e.g., `Forrest Frank Good Day` or `Drake Hotline Bling`)!"
        )
        bot.send_message(message.chat.id, welcome_text, parse_mode="Markdown", reply_markup=get_main_menu_keyboard())
    except Exception as e:
        print(f"[ERROR] Start failed: {e}")

@bot.message_handler(func=lambda message: True)
def handle_song_search(message):
    def worker():
        status_msg = None
        try:
            user_input = message.text.strip()
            if not user_input:
                return

            if user_input == "✨ Search Any Artist / Song":
                bot.send_message(
                    message.chat.id, 
                    "📝 Send the name of the artist and the song you're looking for right here into the chat box!",
                    reply_markup=get_main_menu_keyboard()
                )
                return

            status_msg = bot.reply_to(message, f"🔍 Searching global databases for '{user_input}'...")
            
            # Fetch directly using the open-source web engine
            lyrics = fetch_any_lyrics(user_input)
            
            if len(lyrics) > 4000:
                lyrics = lyrics[:4000] + "\n\n...[Text split due to space limits]..."
            
            try:
                bot.delete_message(message.chat.id, status_msg.message_id)
            except Exception:
                pass 
                
            bot.send_message(message.chat.id, lyrics, parse_mode="Markdown", reply_markup=get_main_menu_keyboard())
        except Exception as e:
            print(f"[ERROR] Chat processing exception: {e}")

    threading.Thread(target=worker).start()

# ==========================================
# SERVER HEALTH MONITOR (Render Port Binding)
# ==========================================
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Search Engine Engine Online!")
    def log_message(self, format, *args): return

def run_health_server():
    HTTPServer(("0.0.0.0", 10000), HealthCheckHandler).serve_forever()

if __name__ == "__main__":
    threading.Thread(target=run_health_server, daemon=True).start()
    while True:
        try:
            bot.infinity_polling(timeout=20, long_polling_timeout=10)
        except Exception:
            time.sleep(5)
