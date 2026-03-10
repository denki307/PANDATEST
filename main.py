import asyncio
import logging
import os
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pytgcalls import PyTgCalls
from pytgcalls.types import AudioPiped, AudioVideoPiped
from yt_dlp import YoutubeDL

# Config file-la irunthu details import pannikurom
from config import (
    API_ID, 
    API_HASH, 
    STRING_SESSION, 
    OWNER_ID, 
    OWNER_USERNAME, 
    SUPPORT_GROUP, 
    CHANNEL_LINK, 
    START_IMG,
    LOGGER_GROUP # Inga unga Logger Group ID (Example: -100xxx) config.py-la add panniko
)

# --- LOGGING SETUP ---
# Ithu thaan errors-ah oru file-la save pannum
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("bot_logs.txt"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Userbot Client Setup
app = Client("VCBot", api_id=API_ID, api_hash=API_HASH, session_string=STRING_SESSION)
call_py = PyTgCalls(app)

# YouTube Search Logic Options
ytdl_audio_opts = {"format": "bestaudio/best", "quiet": True, "geo_bypass": True, "nocheckcertificate": True}
ytdl_video_opts = {"format": "best[height<=720]/best", "quiet": True, "geo_bypass": True, "nocheckcertificate": True}

# --- BUTTONS SETUP ---
START_BUTTONS = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton("Owner 👤", url=f"https://t.me/{OWNER_USERNAME.replace('@','')}")],
        [
            InlineKeyboardButton("Support 💬", url=SUPPORT_GROUP),
            InlineKeyboardButton("Channel 📢", url=CHANNEL_LINK)
        ]
    ]
)

# --- COMMANDS ---

@app.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message):
    await message.reply_photo(
        photo=START_IMG,
        caption=(
            "🔥 **Vanakkam Macha! Bot is Online.**\n\n"
            "🎵 **/play** - Audio Only\n"
            "🎥 **/vplay** - Video + Audio\n"
            "🛑 **/vstop** - Stop stream\n"
            "🛡 **/sudolist** - Owner info\n"
            "📄 **/logs** - Get error file (Owner Only)"
        ),
        reply_markup=START_BUTTONS
    )

@app.on_message(filters.command("sudolist"))
async def sudo_list(client, message):
    await message.reply_text(
        f"🛡 **Sudo/Owner List**\n\n"
        f"👑 **Owner ID:** `{OWNER_ID}`\n"
        f"👤 **Username:** {OWNER_USERNAME}",
        reply_markup=START_BUTTONS
    )

# --- LOGS COMMAND (/logs) ---
@app.on_message(filters.command("logs") & filters.user(OWNER_ID))
async def get_logs(client, message):
    if os.path.exists("bot_logs.txt"):
        await message.reply_document(
            document="bot_logs.txt", 
            caption="📄 Macha, itho bot-oda error logs file!"
        )
    else:
        await message.reply_text("❌ Logs file innum create aagala macha.")

# --- AUDIO PLAY (/play) ---
@app.on_message(filters.command("play") & filters.group)
async def play_audio(client, message):
    if len(message.command) < 2:
        return await message.reply("Enna song venum macha?")

    query = " ".join(message.command[1:])
    m = await message.reply("🎧 Searching Audio...")

    try:
        with YoutubeDL(ytdl_audio_opts) as ytdl:
            info = ytdl.extract_info(f"ytsearch:{query}", download=False)['entries'][0]
            url = info['url']
            title = info['title']
        
        await m.edit(f"🎶 **Playing Audio:** {title}", reply_markup=START_BUTTONS)
        await call_py.join_group_call(message.chat.id, AudioPiped(url))
    except Exception as e:
        logger.error(f"Play Error: {e}")
        await client.send_message(LOGGER_GROUP, f"❌ **Play Error:**\n`{e}`")
        await m.edit(f"❌ Error occurred! Logs-ah check pannu macha.")

# --- VIDEO PLAY (/vplay) ---
@app.on_message(filters.command("vplay") & filters.group)
async def play_video(client, message):
    if len(message.command) < 2:
        return await message.reply("Enna video venum macha?")

    query = " ".join(message.command[1:])
    m = await message.reply("🎥 Searching Video...")

    try:
        with YoutubeDL(ytdl_video_opts) as ytdl:
            info = ytdl.extract_info(f"ytsearch:{query}", download=False)['entries'][0]
            url = info['url']
            title = info['title']
        
        await m.edit(f"🎬 **Streaming Video:** {title}", reply_markup=START_BUTTONS)
        await call_py.join_group_call(message.chat.id, AudioVideoPiped(url))
    except Exception as e:
        logger.error(f"VPlay Error: {e}")
        await client.send_message(LOGGER_GROUP, f"❌ **VPlay Error:**\n`{e}`")
        await m.edit(f"❌ Video Error occurred! Logs check pannu.")

# --- CONTROL COMMANDS ---

@app.on_message(filters.command(["vstop", "stop"]) & filters.group)
async def vstop_command(client, message):
    try:
        await call_py.leave_group_call(message.chat.id)
        await message.reply("👋 Stopped and Left VC!")
    except Exception as e:
        logger.error(f"Stop Error: {e}")

@app.on_message(filters.command(["vpause", "pause"]) & filters.group)
async def vpause_command(client, message):
    try:
        await call_py.pause_stream(message.chat.id)
        await message.reply("⏸ Paused.")
    except Exception as e:
        logger.error(f"Pause Error: {e}")

@app.on_message(filters.command(["vresume", "resume"]) & filters.group)
async def vresume_command(client, message):
    try:
        await call_py.resume_stream(message.chat.id)
        await message.reply("▶️ Resumed.")
    except Exception as e:
        logger.error(f"Resume Error: {e}")

# --- BOT STARTUP ---

async def start_bot():
    await app.start()
    await call_py.start()
    print("✅ VC Bot is Live with Logger Support!")
    await asyncio.Event().wait()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(start_bot())
    except KeyboardInterrupt:
        pass
