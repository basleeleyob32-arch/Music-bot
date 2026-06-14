import os
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
import time
import telebot
from telebot import types
import lyricsgenius

# ==========================================
# CORE CONFIGURATION
# ==========================================
BOT_TOKEN = "8747299464:AAFqYZTvm0Sh8tFDOcqj8UioBcrtnO2P4y8"
CHANNEL_ID = "-1002375727016"  # Your music channel ID

# Replace with the real token you get from genius.com/api-clients
GENIUS_TOKEN = "SrbNKao86j7f8W-IL_dtD_JBHVROKGw6yiRpkze5Y5mtxLu57jZMvxxPQLo5lZeZ"

bot = telebot.TeleBot(BOT_TOKEN, threaded=True)
genius = lyricsgenius.Genius(GENIUS_TOKEN, timeout=15, retries=3)

# Strip out unnecessary web clutter for clean Telegram delivery
genius.remove_section_headers = True  
genius.skip_non_songs = True          

# ==========================================
# INTERACTIVE CUSTOM USER INTERFACE
# ==========================================
def get_main_menu_keyboard():
    """Generates a clean, scannable custom keyboard for your subscribers."""
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = types.KeyboardButton("☀️ Good Day")
    btn2 = types.KeyboardButton("⚓ No Longer Bound")
    btn3 = types.KeyboardButton("🔥 Never Walk Alone")
    btn4 = types.KeyboardButton("🤍 Always")
    btn5 = types.KeyboardButton("🎵 Child of God")
    btn6 = types.KeyboardButton("✨ Search Another Song")
    markup.add(btn1, btn2, btn3, btn4, btn5, btn6)
    return markup

def get_join_channel_keyboard():
    """Creates an inline button guiding non-subscribers straight to your channel link."""
    markup = types.InlineKeyboardMarkup()
    # Replace with your actual public channel invite username link if needed
    btn_link = types.InlineKeyboardButton("📢 Join Music Channel", url="https://t.me/c/2375727016/1")
    markup.add(btn_link)
    return markup

# ==========================================
# SECURITY: CHANNEL MEMBERSHIP VERIFICATION
# ==========================================
def is_subscribed(user_id):
    """Verifies if the user is a current member of your Telegram channel community."""
    try:
        member = bot.get_chat_member(CHANNEL_ID, user_id)
        if member.status in ['member', 'administrator', 'creator']:
            return True
        return False
    except Exception as e:
        print(f"[SECURITY ERROR] Membership verification bypassed/failed: {e}")
        # Default safety fallback: let them through if the API handshake hit a snag
        return True

# ==========================================
# GENIUS DATABASE ENGINE WITH ARTIST LOCKDOWN
# ==========================================
def fetch_forrest_frank_lyrics(song_title):
    try:
        # Strict internal lookup rule: Force the query context specifically onto Forrest Frank
        song = genius.search_song(song_title, "Forrest Frank")
        
        if song and "forrest frank" in song.artist.lower():
            clean_lyrics = song.lyrics.split("Embed")[0]
            if clean_lyrics.startswith(song.title):
                clean_lyrics = clean_lyrics[len(song.title):].strip()
                
            return f"🎵 **LYRICS: {song.title.upper()}** 🎵\nBy Forrest Frank\n\n{clean_lyrics}"
        else:
            return f"❌ Couldn't find a matching Forrest Frank song named '{song_title}'. Double check your spelling!"
    except Exception as e:
        print(f"[API ERROR] Database handshake failure: {e}")
        return "⚠️ The lyrics database is currently experiencing heavy traffic. Please try tapping again in a few seconds!"

# ==========================================
# TELEGRAM ACTION ROUTERS
# ==========================================
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    try:
        if not is_subscribed(message.from_user.id):
            bot.send_message(
                message.chat.id,
                "👋 *Welcome!*\n\nThis premium lyrics bot is exclusively reserved for members of our music channel. Please join the channel below to unlock access!",
                parse_mode="Markdown",
                reply_markup=get_join_channel_keyboard()
            )
            return

        welcome_text = (
            f"👋 *Welcome to the Official Forrest Frank Lyrics Bot!*\n\n"
            f"Verified Subscriber Access Authorized! 🎉\n\n"
            f"👉 **How to use me:**\n"
            f"• Tap any of the quick-access hotkeys below.\n"
            f"• Or type any specific **Forrest Frank song name** directly into the chat box!"
        )
        bot.send_message(message.chat.id, welcome_text, parse_mode="Markdown", reply_markup=get_main_menu_keyboard())
    except Exception as e:
        print(f"[ERROR] UI start failure: {e}")

@bot.message_handler(func=lambda message: True)
def handle_song_search(message):
    def worker():
        status_msg = None
        try:
            # 1. Double check security gate on every single query text transaction
            if not is_subscribed(message.from_user.id):
                bot.send_message(
                    message.chat.id,
                    "⚠️ *Access Restricted!*\n\nYou must be a member of our music channel to fetch lyrics. Please join below!",
                    parse_mode="Markdown",
                    reply_markup=get_join_channel_keyboard()
                )
                return

            user_input = message.text.strip()
            if not user_input:
                return

            if user_input == "✨ Search Another Song":
                bot.send_message(message.chat.id, "📝 Just type the name of any other Forrest Frank song directly into the chat box!", reply_markup=get_main_menu_keyboard())
                return

            # Clean UI cosmetic emoji indicators out of string queries
            search_query = user_input
            for emoji in ["☀️ ", "⚓ ", "🔥 ", "🤍 ", "🎵 "]:
                search_query = search_query.replace(emoji, "")

            status_msg = bot.reply_to(message, f"🔍 Querying global archives for Forrest Frank's '{search_query}'...")
            
            # 2. Fetch lyrics securely
            lyrics = fetch_forrest_frank_lyrics(search_query)
            
            if len(lyrics) > 4000:
                lyrics = lyrics[:4000] + "\n\n...[Lyrics split due to platform limitations]..."
            
            try:
                bot.delete_message(message.chat.id, status_msg.message_id)
            except Exception:
                pass 
                
            bot.send_message(message.chat.id, lyrics, parse_mode="Markdown", reply_markup=get_main_menu_keyboard())
        except Exception as e:
            print(f"[THREAD ERROR] {e}")

    threading.Thread(target=worker).start()

# ==========================================
# HEALTH PINBACK SERVER (Render Requirement)
# ==========================================
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Forrest Frank Engine Active!")
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

            
