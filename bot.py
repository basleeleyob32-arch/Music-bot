import os
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

import requests
import telebot
from telebot import types

# ==========================================
# CONFIGURATION
# ==========================================

BOT_TOKEN = "8747299464:AAG5JWw3SLYDbf4ydp4Stz5jTxTk7oM1CE0"
CHANNEL_ID = "-1002375727016"

bot = telebot.TeleBot(BOT_TOKEN, threaded=True)

# ==========================================
# KEYBOARDS
# ==========================================

def get_main_menu_keyboard():
    markup = types.ReplyKeyboardMarkup(
        row_width=2,
        resize_keyboard=True
    )

    markup.add(
        types.KeyboardButton("☀️ Good Day"),
        types.KeyboardButton("⚓ No Longer Bound")
    )

    markup.add(
        types.KeyboardButton("🔥 Never Walk Alone"),
        types.KeyboardButton("🤍 Always")
    )

    markup.add(
        types.KeyboardButton("🎵 Child of God"),
        types.KeyboardButton("✨ Search Another Song")
    )

    return markup


def get_join_channel_keyboard():
    markup = types.InlineKeyboardMarkup()

    markup.add(
        types.InlineKeyboardButton(
            "📢 Join Music Channel",
            url="https://t.me/c/2375727016/1"
        )
    )

    return markup

# ==========================================
# CHANNEL CHECK
# ==========================================

def is_subscribed(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_ID, user_id)

        return member.status in [
            "member",
            "administrator",
            "creator"
        ]

    except Exception as e:
        print(f"[MEMBERSHIP ERROR] {e}")

        # Allow access if Telegram API temporarily fails
        return True

# ==========================================
# LRCLIB LYRICS ENGINE
# ==========================================

def fetch_forrest_frank_lyrics(song_title):
    try:
        response = requests.get(
            "https://lrclib.net/api/search",
            params={
                "track_name": song_title,
                "artist_name": "Forrest Frank"
            },
            headers={
                "User-Agent": "ForrestFrankLyricsBot/1.0"
            },
            timeout=15
        )

        if response.status_code != 200:
            return (
                "⚠️ Lyrics server returned an error.\n"
                "Please try again later."
            )

        results = response.json()

        if not results:
            return (
                f"❌ Couldn't find '{song_title}'.\n\n"
                "Try typing the exact song title."
            )

        best_match = None

        for song in results:
            artist = song.get("artistName", "").lower()

            if "forrest frank" in artist:
                best_match = song
                break

        if best_match is None:
            best_match = results[0]

        lyrics = best_match.get("plainLyrics")

        if not lyrics:
            return (
                f"❌ Lyrics not available for '{song_title}'."
            )

        if len(lyrics) > 3800:
            lyrics = lyrics[:3800] + "\n\n...[Lyrics truncated]..."

        track_name = best_match.get(
            "trackName",
            song_title
        )

        artist_name = best_match.get(
            "artistName",
            "Forrest Frank"
        )

        return (
            f"🎵 *{track_name}*\n"
            f"👤 {artist_name}\n\n"
            f"{lyrics}"
        )

    except requests.exceptions.Timeout:
        return (
            "⚠️ Lyrics search timed out.\n"
            "Please try again."
        )

    except Exception as e:
        print(f"[LRCLIB ERROR] {e}")

        return (
            "⚠️ Lyrics service temporarily unavailable.\n"
            "Please try again later."
        )

# ==========================================
# START COMMAND
# ==========================================

@bot.message_handler(commands=["start", "help"])
def start_handler(message):
    try:

        if not is_subscribed(message.from_user.id):
            bot.send_message(
                message.chat.id,
                (
                    "👋 Welcome!\n\n"
                    "This lyrics bot is available "
                    "only to channel members."
                ),
                reply_markup=get_join_channel_keyboard()
            )
            return

        bot.send_message(
            message.chat.id,
            (
                "🎵 Forrest Frank Lyrics Bot\n\n"
                "Tap a song below or type any "
                "Forrest Frank song title."
            ),
            reply_markup=get_main_menu_keyboard()
        )

    except Exception as e:
        print(f"[START ERROR] {e}")

# ==========================================
# SONG SEARCH
# ==========================================

@bot.message_handler(func=lambda message: True)
def search_handler(message):

    def worker():

        try:

            if not is_subscribed(message.from_user.id):
                bot.send_message(
                    message.chat.id,
                    (
                        "⚠️ Access Restricted!\n\n"
                        "Join the music channel first."
                    ),
                    reply_markup=get_join_channel_keyboard()
                )
                return

            user_input = message.text.strip()

            if not user_input:
                return

            if user_input == "✨ Search Another Song":
                bot.send_message(
                    message.chat.id,
                    "📝 Type any Forrest Frank song title.",
                    reply_markup=get_main_menu_keyboard()
                )
                return

            search_query = user_input

            emojis = [
                "☀️ ",
                "⚓ ",
                "🔥 ",
                "🤍 ",
                "🎵 "
            ]

            for emoji in emojis:
                search_query = search_query.replace(
                    emoji,
                    ""
                )

            status_message = bot.reply_to(
                message,
                f"🔍 Searching for '{search_query}'..."
            )

            lyrics = fetch_forrest_frank_lyrics(
                search_query
            )

            try:
                bot.delete_message(
                    message.chat.id,
                    status_message.message_id
                )
            except Exception:
                pass

            bot.send_message(
                message.chat.id,
                lyrics,
                parse_mode="Markdown",
                reply_markup=get_main_menu_keyboard()
            )

        except Exception as e:
            print(f"[SEARCH ERROR] {e}")

    threading.Thread(target=worker).start()

# ==========================================
# HEALTH SERVER FOR RENDER
# ==========================================

class HealthCheckHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.send_header(
            "Content-type",
            "text/plain"
        )
        self.end_headers()

        self.wfile.write(
            b"Forrest Frank Lyrics Bot Running"
        )

    def log_message(self, format, *args):
        return


def run_health_server():
    port = int(
        os.environ.get("PORT", 10000)
    )

    server = HTTPServer(
        ("0.0.0.0", port),
        HealthCheckHandler
    )

    print(f"Health server running on {port}")

    server.serve_forever()

# ==========================================
# MAIN
# ==========================================

if __name__ == "__main__":

    threading.Thread(
        target=run_health_server,
        daemon=True
    ).start()

    while True:
        try:
            print("Bot started")

            bot.infinity_polling(
                timeout=20,
                long_polling_timeout=20
            )

        except Exception as e:
            print(f"[POLLING ERROR] {e}")
            time.sleep(5)
