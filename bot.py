import os
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
import time
import requests
import telebot
from telebot import types

# ==========================================
# PERMANENT CONFIGURATION
# ==========================================
# Your verified correct tokens are securely locked in right here
BOT_TOKEN = "8747299464:AAfqYZTvm0Sh8tFDOcqj8UioBcrtn02P4y8"
CHANNEL_ID = "-1002375727016" 

# Initialize Telegram Bot with Multi-Threading enabled
bot = telebot.TeleBot(BOT_TOKEN, threaded=True)

# ==========================================
# INTERACTIVE USER INTERFACE MENU
# ==========================================
def get_main_menu_keyboard():
    """Creates a beautifully organized custom keyboard menu for your users."""
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    
    # Quick access macro buttons for Forrest Frank hits
    btn1 = types.KeyboardButton("☀️ Good Day")
    btn2 = types.KeyboardButton("⚓ No Longer Bound")
    btn3 = types.KeyboardButton("🔥 Never Walk Alone")
    btn4 = types.KeyboardButton("🤍 Always")
    btn5 = types.KeyboardButton("🎵 Child of God")
    btn6 = types.KeyboardButton("✨ Search Another Song")
    
    markup.add(btn1, btn2, btn3, btn4, btn5, btn6)
    return markup

# ==========================================
# TOKEN-FREE PUBLIC LYRICS SEARCH ENGINE
# ==========================================
def fetch_lyrics_from_public_api(song_title):
    """Fetches lyrics from api.lyrics.ovh without needing any API access tokens."""
    try:
        artist_name = "Forrest Frank"
        # Standardize spaces for a clean web request URL structure
        url = f"https://api.lyrics.ovh/v1/{artist_name}/{song_title}"
        
        # Pull request with an integrated 10-second server timeout protection
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            lyrics_text = data.get("lyrics", "").strip()
            
            if lyrics_text:
                return f"🎵 **LYRICS: {song_title.upper()}** 🎵\nBy Forrest Frank\n\n{lyrics_text}"
            
        return f"❌ Couldn't find lyrics for '{song_title}' by Forrest Frank. Double check the spelling and try again!"
        
    except requests.exceptions.Timeout:
        return "⚠️ The network connection timed out. Please try tapping the button again!"
    except Exception as e:
        print(f"[ERROR] Public API lookup failure: {e}")
        return "⚠️ Could not grab lyrics right now. Let's try that song query once more!"

# ==========================================
# TELEGRAM BOT HANDLERS
# ==========================================
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    try:
        welcome_text = (
            f"👋 *Welcome to the Official Forrest Frank Lyrics Bot!*\n\n"
            f"Brought to you by your favorite music channel. I am now using an open public database network!\n\n"
            f"👉 **How to use me:**\n"
            f"• Tap any of the quick-access buttons below to fetch lyrics instantly.\n"
            f"• Or simply **type any song name** directly into the chat bar!"
        )
        bot.send_message(
            message.chat.id, 
            welcome_text, 
            parse_mode="Markdown", 
            reply_markup=get_main_menu_keyboard()
        )
    except Exception as e:
        print(f"[ERROR] Welcome message menu failed: {e}")

@bot.message_handler(func=lambda message: True)
def handle_song_search(message):
    def worker():
        status_msg = None
        try:
            user_input = message.text.strip()
            if not user_input:
                return

            # UI Action: Handle menu text helper gracefully
            if user_input == "✨ Search Another Song":
                bot.send_message(
                    message.chat.id, 
                    "📝 Just type the exact name of the song you want to find right here into the chat box!",
                    reply_markup=get_main_menu_keyboard()
                )
                return

            # Strip emoji formatting if they used the native macro menu layout
            search_query = user_input
            for emoji in ["☀️ ", "⚓ ", "🔥 ", "🤍 ", "🎵 "]:
                search_query = search_query.replace(emoji, "")

            # 1. Provide live visual loading feedback to user
            status_msg = bot.reply_to(message, f"🔍 Searching database for '{search_query}'...")
            
            # 2. Fetch data via the open source API link
            lyrics = fetch_lyrics_from_public_api(search_query)
            
            # 3. Size protection to ensure delivery fits Telegram specs
            if len(lyrics) > 4000:
                lyrics = lyrics[:4000] + "\n\n...[Lyrics split due to system size limitations]..."
            
            # 4. Remove loading screen placeholder safely
            try:
                bot.delete_message(message.chat.id, status_msg.message_id)
            except Exception:
                pass 
                
            # 5. Send out final text output block
            bot.send_message(
                message.chat.id, 
                lyrics, 
                parse_mode="Markdown",
                reply_markup=get_main_menu_keyboard()
            )
            
        except Exception as general_error:
            print(f"[ERROR] Active thread failure: {general_error}")
            try:
                bot.send_message(
                    message.chat.id, 
                    "⚠️ Connection hit a temporary snag. Let's try that request once more!",
                    reply_markup=get_main_menu_keyboard()
                )
            except Exception:
                pass

    threading.Thread(target=worker).start()

# ==========================================
# HEALTH CHECK MONITOR (Render Web Requirement)
# ==========================================
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Bot Server Engine is Active!")
        except Exception as e:
            print(f"[ERROR] Port pingback failure: {e}")

    def log_message(self, format, *args):
        return 

def run_health_server():
    try:
        server = HTTPServer(("0.0.0.0", 10000), HealthCheckHandler)
        server.serve_forever()
    except Exception as e:
        print(f"[CRITICAL] Health check socket failed to open: {e}")

# ==========================================
# MAIN EXECUTION AND RE-POLLING PROTECTION
# ==========================================
if __name__ == "__main__":
    print("Binding background health listener to port 10000...")
    threading.Thread(target=run_health_server, daemon=True).start()
    
    print("Public API Lyrics Bot engine is running...")
    
    while True:
        try:
            bot.infinity_polling(timeout=20, long_polling_timeout=10)
        except Exception as crash_error:
            print(f"[WARNING] Server drop protected: {crash_error}. Restarting in 5 seconds...")
            time.sleep(5)
                    
