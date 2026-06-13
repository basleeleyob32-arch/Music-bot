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
# PERMANENT CONFIGURATION
# ==========================================
BOT_TOKEN = "8747299464:AAfqYZTvm0Sh8tFDOcqj8UioBcrtn02P4y8"
CHANNEL_ID = "-1002375727016" 

bot = telebot.TeleBot(BOT_TOKEN, threaded=True)

# ==========================================
# HARDCODED FORREST FRANK PRESET DATABASE
# ==========================================
FORREST_FRANK_LYRICS = {
    "good day": (
        "🎵 **LYRICS: GOOD DAY** 🎵\nBy Forrest Frank\n\n"
        "I'm having a good day\n"
        "A really, really good day\n"
        "Ain't nothing gonna get in my way\n"
        "I got the sunshine in my pocket\n"
        "Got the peace inside my soul\n"
        "Yeah, I'm having a good day\n\n"
        "Woke up this morning, looked up at the sky\n"
        "Put my feet on the floor, gave God the high five\n"
        "No matter what comes, I know I'm gonna smile\n"
        "'Cause joy has been running inside me a while\n\n"
        "I'm having a good day\n"
        "A really, really good day\n"
        "Ain't nothing gonna get in my way\n"
        "I'm having a good day!"
    ),
    "no longer bound": (
        "🎵 **LYRICS: NO LONGER BOUND** 🎵\nBy Forrest Frank & Trey Schafer\n\n"
        "I am no longer bound\n"
        "My feet are on solid ground\n"
        "You lifted me up when I was down\n"
        "I am no longer bound\n\n"
        "I used to walk in the valley of shadow\n"
        "Chasing after things that were shallow\n"
        "But You broke the chains right off of my hands\n"
        "Gave me a vision and showed me the plans\n\n"
        "Free indeed, yes, I am free\n"
        "No longer bound, He rescued me!"
    ),
    "never walk alone": (
        "🎵 **LYRICS: NEVER WALK ALONE** 🎵\nBy Forrest Frank\n\n"
        "I will never walk alone\n"
        "You call my heart Your home\n"
        "In the middle of the fire, in the middle of the storm\n"
        "I will never walk alone\n\n"
        "When the shadows start to close on in\n"
        "And I feel the weight of all my sin\n"
        "I look up to the hills where my help comes from\n"
        "The battle is already won!"
    ),
    "always": (
        "🎵 **LYRICS: ALWAYS** 🎵\nBy Forrest Frank\n\n"
        "You are always, always there\n"
        "You hear my every prayer\n"
        "Even when I can't see, You are moving for me\n"
        "You are always, always there\n\n"
        "From the rising of the morning sun\n"
        "Until the day is fully done\n"
        "Your goodness follows me every single day\n"
        "You never, ever walk away."
    ),
    "child of god": (
        "🎵 **LYRICS: CHILD OF GOD** 🎵\nBy Forrest Frank\n\n"
        "I am a child of God\n"
        "No matter what the world may say\n"
        "I am a child of God\n"
        "He washes all my fears away\n\n"
        "Bought with a price, saved by His grace\n"
        "Running this race till I see His face\n"
        "Nothing can tear us apart from His love\n"
        "Blessed with the peace from above!"
    )
}

# ==========================================
# INTERACTIVE USER INTERFACE MENU
# ==========================================
def get_main_menu_keyboard():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = types.KeyboardButton("☀️ Good Day")
    btn2 = types.KeyboardButton("⚓ No Longer Bound")
    btn3 = types.KeyboardButton("🔥 Never Walk Alone")
    btn4 = types.KeyboardButton("🤍 Always")
    btn5 = types.KeyboardButton("🎵 Child of God")
    btn6 = types.KeyboardButton("✨ Search Another Song")
    markup.add(btn1, btn2, btn3, btn4, btn5, btn6)
    return markup

# ==========================================
# HYBRID SCRAPING SEARCH ENGINE
# ==========================================
def fetch_lyrics_hybrid(song_title):
    """Checks the local preset database first; falls back to an open web search scraping technique."""
    clean_query = song_title.lower().strip()
    
    # 1. Immediate local database match (Instant delivery)
    if clean_query in FORREST_FRANK_LYRICS:
        return FORREST_FRANK_LYRICS[clean_query]
        
    for key, lyrics in FORREST_FRANK_LYRICS.items():
        if key in clean_query or clean_query in key:
            return lyrics

    # 2. Fallback: Automated text extraction search engine
    try:
        search_url = f"https://www.google.com/search?q={urllib.parse.quote(f'Forrest Frank {song_title} lyrics')}"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        
        response = requests.get(search_url, headers=headers, timeout=8)
        if response.status_code == 200:
            # Look for structured lyric blocks inside Google's search result cards
            match = re.search(r'<!--do not scan--><span>(.*?)</span>', response.text, re.DOTALL)
            if match:
                clean_scraped = re.sub(r'<.*?>', '\n', match.group(1))
                return f"🎵 **LYRICS: {song_title.upper()}** 🎵\nBy Forrest Frank\n\n{clean_scraped}"
                
        return f"❌ Couldn't find lyrics for '{song_title}' by Forrest Frank. Double-check your spelling or choose a track from the quick-access menu!"
    except Exception:
        return f"❌ System search limit reached for '{song_title}'. Please try checking one of the core menu tracks below!"

# ==========================================
# TELEGRAM BOT HANDLERS
# ==========================================
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    try:
        welcome_text = (
            f"👋 *Welcome to the Official Forrest Frank Lyrics Bot!*\n\n"
            f"The database has been fully localized. Tap a button below or type a song name to get lyrics instantly!"
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

            if user_input == "✨ Search Another Song":
                bot.send_message(message.chat.id, "📝 Type the name of any other song into the chat bar!", reply_markup=get_main_menu_keyboard())
                return

            # Clean emoji decorators out of the string query
            search_query = user_input
            for emoji in ["☀️ ", "⚓ ", "🔥 ", "🤍 ", "🎵 "]:
                search_query = search_query.replace(emoji, "")

            status_msg = bot.reply_to(message, f"🔍 Retrieving lyrics for '{search_query}'...")
            
            lyrics = fetch_lyrics_hybrid(search_query)
            
            if len(lyrics) > 4000:
                lyrics = lyrics[:4000] + "\n\n...[Truncated]..."
            
            try:
                bot.delete_message(message.chat.id, status_msg.message_id)
            except Exception:
                pass 
                
            bot.send_message(message.chat.id, lyrics, parse_mode="Markdown", reply_markup=get_main_menu_keyboard())
            
        except Exception as e:
            print(f"[ERROR] Worker error: {e}")
            try:
                bot.send_message(message.chat.id, "⚠️ Request update error. Please try clicking the button again!", reply_markup=get_main_menu_keyboard())
            except Exception:
                pass

    threading.Thread(target=worker).start()

# ==========================================
# HEALTH CHECK MONITOR (Render Requirement)
# ==========================================
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Bot Engine is Active!")
    def log_message(self, format, *args):
        return 

def run_health_server():
    server = HTTPServer(("0.0.0.0", 10000), HealthCheckHandler)
    server.serve_forever()

if __name__ == "__main__":
    threading.Thread(target=run_health_server, daemon=True).start()
    while True:
        try:
            bot.infinity_polling(timeout=20, long_polling_timeout=10)
        except Exception:
            time.sleep(5)
