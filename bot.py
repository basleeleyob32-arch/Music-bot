import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from telegram.error import BadRequest

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- CONFIGURATION ---
BOT_TOKEN = "8747299464:AAESNSeAMaCJAFD-jIuNQeyZp2dJDMausO0"
# The channel ID must start with -100. (e.g., -100123456789)
# Tip: Add your bot to the channel as an ADMINISTRATOR so it can check member status.
CHANNEL_ID = "-1002375727016" 
CHANNEL_INVITE_LINK = "https://t.me/forrestfranksongs"

# A simple hardcoded database of lyrics for demonstration.
# In production, you can connect this to an external API (like Genius) or a database.
LYRICS_DATABASE = {
    "blinding lights": "I've been tryna call...\nI've been on my own for long enough...",
    "shape of you": "The club isn't the best place to find a lover...\nSo the bar is where I go...",
    "bohemian rhapsody": "Is this the real life?\nIs this just fantasy?..."
}

async def is_user_subscribed(bot, user_id: int) -> bool:
    """Checks if the user is a member, administrator, or creator of the target channel."""
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        if member.status in ["member", "administrator", "creator"]:
            return True
        return False
    except BadRequest as e:
        # Handles cases where the bot configuration or user ID might be invalid
        logger.error(f"Error checking chat member: {e}")
        return False

async def send_join_request_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends a message with a button linking to the channel and a verify button."""
    keyboard = [
        [InlineKeyboardButton("📢 Join Channel", url=CHANNEL_INVITE_LINK)],
        [InlineKeyboardButton("✅ I have joined!", callback_data="check_subscription")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = "⚠️ **Access Denied!**\n\nYou must join our official channel first before you can use this bot to get lyrics."
    
    if update.message:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    elif update.callback_query:
        await update.callback_query.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /start command."""
    user_id = update.effective_user.id
    
    if await is_user_subscribed(context.bot, user_id):
        await update.message.reply_text(
            "👋 Welcome to the Lyrics Bot! Send me the name of a song, and I'll find the lyrics for you."
        )
    else:
        await send_join_request_message(update, context)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processes lyrics requests only if the user is subscribed."""
    user_id = update.effective_user.id
    
    if not await is_user_subscribed(context.bot, user_id):
        await send_join_request_message(update, context)
        return

    song_query = update.message.text.lower().strip()
    await update.message.reply_text(f"🔍 Searching for lyrics to: '{update.message.text}'...")

    # Look up lyrics in our dummy database
    if song_query in LYRICS_DATABASE:
        await update.message.reply_text(f"🎵 **Lyrics for {update.message.text}:**\n\n{LYRICS_DATABASE[song_query]}", parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ Sorry, I couldn't find lyrics for that song. Try 'Blinding Lights' or 'Shape of You'!")

async def check_subscription_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the inline button click verifying subscription."""
    query = update.callback_query
    await query.answer() # Acknowledge button click
    
    user_id = query.from_user.id
    
    if await is_user_subscribed(context.bot, user_id):
        await query.message.delete() # Clean up the join prompt
        await context.bot.send_message(
            chat_id=user_id,
            text="🎉 Thank you for joining! You now have full access. Send me a song name to get started!"
        )
    else:
        # Alert banner at top of Telegram screen
        await query.answer("❌ You still haven't joined the channel. Please join first!", show_alert=True)

def main():
    """Starts the bot."""
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE" or CHANNEL_ID == "-100XXXXXXXXXXXXXXXX":
        print("Please configure your BOT_TOKEN and CHANNEL_ID before running.")
        return

    application = Application.builder().token(BOT_TOKEN).build()

    # Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(check_subscription_callback, pattern="^check_subscription$"))
    # Handle all text messages except commands
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Run the bot until Ctrl-C is pressed
    print("Bot is running...")
    application.run_polling()

if __name__ == "__main__":
    main()
