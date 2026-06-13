import os
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
import time
import telebot
from telebot import types
import lyricsgenius

# ==========================================
# PERMANENT CONFIGURATION
# ==========================================
BOT_TOKEN = "8747299464:AAFqYZTvm0Sh8tFDOcqj8UioBcrtnO2P4y8"
CHANNEL_ID = "-1002375727016" 
GENIUS_TOKEN = "L69NI1b_IIx1lCWGcNxKhGt2ciPdcHBV7o6bFbSprFUBCAvIUExbEXdm_97Ylowi"

# Initialize Clients with Advanced Stability Settings
bot = telebot.TeleBot(BOT_TOKEN, threaded=True)
genius = lyricsgenius.Genius(GENIUS_TOKEN, timeout=15, retries=3)

# Clean up Genius outputs automatically
genius.remove_section_headers = True  
genius.skip_non_songs = True          

# ==========================================
# INTERACTIVE USER INTERFACE MENU
# ==========================================
def get_main_menu_keyboard():
    """Creates a beautifully organized custom keyboard menu for your users."""
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    
    # Quick access buttons for Forrest Frank's biggest hits and albums
    btn1 = types.KeyboardButton("☀️ Good Day")
    btn2 = types.KeyboardButton("⚓ No Longer Bound")
    btn3 = types.KeyboardButton("🔥 Never Walk Alone")
    btn4 = types.KeyboardButton("🤍 Always")
    btn5 = types.KeyboardButton("🎵 Child of God (Album)")
    btn6 = types.KeyboardButton("✨ Search Another Song")
    
    markup.add(btn1, btn2, btn3, btn4, btn5, btn6)
    return markup

# ==========================================
# SAFE LYRICS FETCHING FUNCTION
# ==========================================
def fetch_lyrics_safe(song_title):
    """Searches Genius database smoothly and applies professional string formatting."""
    try:
        # Standardize search query to stick directly to Forrest Frank
        song = genius.search_song(song_title, "Forrest Frank")
        
        if song:
            # Clean up metadata text that Genius appends to the end
            clean_lyrics = song.lyrics.split("Embed")[0]
            
            # Remove any repeating title headers at the very top of the text block
            if clean_lyrics.startswith(song.title):
                clean_lyrics = clean_lyrics[len(song.title):].strip()
                
            return f"🎵 **LYRICS: {song.title.upper()}** 🎵\nBy Forrest Frank\n\n{clean_lyrics}"
        else:
            return f"❌ Couldn't find lyrics for '{song_title}' by Forrest Frank on Genius. Double check the spelling and try again!"
            
    except Exception as e:
        print(f"[ERROR] Genius API Connection issue: {e}")
        return "⚠️ The lyrics database is experiencing high traffic. Please try pressing the button again in a few seconds!"

# ==========================================
# TELEGRAM BOT HANDLERS
# ==========================================
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    try:
        welcome_text = (
            f"👋 *Welcome to the Official Forrest Frank Lyrics Bot!*\n\n"
            f"Brought to you by your favorite music channel. I am connected directly to a live global database.\n\n"
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

            # UI Action: Handle menu helper text gracefully
            if user_input == "✨ Search Another Song":
                bot.send_message(
                    message.chat.id, 
                    "📝 Just type the exact name of the song you want to find right here into the chat box!",
                    reply_markup=get_main_menu_keyboard()
                )
                return

            # Clean up internal naming structure if they tapped an album macro button
            search_query = user_input
            if "☀️ " in search_query or "⚓ " in search_query or "🔥 " in search_query or "🤍 " in search_query:
                search_query = user_input.replace("☀️ ", "").replace("⚓ ", "").replace("🔥 ", "").replace("🤍 ", "")
            elif "Child of God" in search_query:
                search_query = "Child of God"

            # 1. Provide dynamic loading visual confirmation
            status_msg = bot.reply_to(message, f"🔍 Connecting to API... Fetching lyrics for '{search_query}'...")
            
            # 2. Safely query the Genius Client Access Network
            lyrics = fetch_lyrics_safe(search_query)
            
            # 3. Guardrail implementation against Telegram's strict character limitations
            if len(lyrics) > 4000:
                lyrics = lyrics[:4000] + "\n\n...[Lyrics split due to system size limitations]..."
            
            # 4. Wipe loading screen placeholder text safely
            try:
                bot.delete_message(message.chat.id, status_msg.message_id)
            except Exception:
                pass 
                
            # 5. Deliver final lyric block with original menu layout preserved
            bot.send_message(
                message.chat.id, 
                lyrics, 
                parse_mode="Markdown",
                reply_markup=get_main_menu_keyboard()
            )
            
        except Exception as general_error:
            print(f"[ERROR] Active connection worker failure: {general_error}")
            try:
                bot.send_message(
                    message.chat.id, 
                    "⚠️ Connection timed out briefly. Let's try that request once more!",
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
            self.wfile.write(b"Bot Interface is Live!")
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
# MAIN EXECUTION AND CRASH SHELTER
# ==========================================
if __name__ == "__main__":
    print("Binding background listener to port 10000...")
    threading.Thread(target=run_health_server, daemon=True).start()
    
    print("Premium Interface Bot is running...")
    
    while True:
        try:
            bot.infinity_polling(timeout=20, long_polling_timeout=10)
        except Exception as crash_error:
            print(f"[WARNING] Server restart protection triggered: {crash_error}. Re-polling in 5 seconds...")
            time.sleep(5)

