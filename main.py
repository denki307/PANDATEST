import asyncio
import logging
import os
import requests
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pytgcalls import PyTgCalls
from pytgcalls.types import AudioPiped, AudioVideoPiped
from yt_dlp import YoutubeDL

# Config file-la irunthu details import pannikurom
from config import (
    API_ID, 
    API_HASH, 
    BOT_TOKEN,
    STRING_SESSION, 
    OWNER_ID, 
    OWNER_USERNAME, 
    SUPPORT_GROUP, 
    CHANNEL_LINK, 
    START_IMG,
    LOGGER_GROUP,
    YOUTUBE_API_KEY
)

# --- LOGGING SETUP ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("bot_logs.txt"), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# --- CLIENTS SETUP ---
# 1. Bot Client: Commands handle panna (Token use pannum)
bot = Client("MusicBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# 2. Userbot Client: VC-la join panni stream panna (Session use pannum)
user = Client("Userbot", api_id=API_ID, api_hash=API_HASH, session_string=STRING_SESSION)

call_py = PyTgCalls(user)

# --- YOUTUBE API SEARCH FUNCTION ---
def youtube_search(query):
    try:
        url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q={query}&maxResults=1&type=video&key={YOUTUBE_API_KEY}"
        response = requests.get(url).json()
        if "items" not in response or not response['items']:
            return None, None
        video_id = response['items'][0]['id']['videoId']
        title = response['items'][0]['snippet']['title']
        return video_id, title
    except Exception as e:
        logger.error(f"YouTube API Error: {e}")
        return None, None

# YouTube DL Options
ytdl_audio_opts = {"format": "bestaudio/best", "quiet": True, "nocheckcertificate": True}
ytdl_video_opts = {"format": "best[height<=720]/best", "quiet": True, "nocheckcertificate": True}

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

# --- COMMANDS (Bot Client-la handle aagum) ---

@bot.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message):
    await message.reply_photo(
        photo=START_IMG,
        caption=(
            "🔥 **Vanakkam Macha! Dual-Client Bot Live.**\n\n"
            "🎵 **/play** - Audio Only (YouTube API)\n"
            "🎥 **/vplay** - Video + Audio (YouTube API)\n"
            "🛑 **/vstop** - Stop & Leave VC\n"
            "⏸ **/vpause** - Pause | ▶️ **/vresume** - Resume\n"
            "🛡 **/sudolist** - Owner info\n"
            "📄 **/logs** - Get error file (Owner Only)"
        ),
        reply_markup=START_BUTTONS
    )

@bot.on_message(filters.command("sudolist"))
async def sudo_list(client, message):
    await message.reply_text(
        f"🛡 **Sudo/Owner List**\n\n🆔 **Owner ID:** `{OWNER_ID}`\n👤 **Username:** {OWNER_USERNAME}",
        reply_markup=START_BUTTONS
    )

@bot.on_message(filters.command("logs") & filters.user(OWNER_ID))
async def get_logs(client, message):
    if os.path.exists("bot_logs.txt"):
        await message.reply_document(document="bot_logs.txt", caption="📄 Bot Error Logs")
    else:
        await message.reply_text("❌ Logs file ready-ah illa.")

# --- AUDIO PLAY (/play) ---
@bot.on_message(filters.command("play") & filters.group)
async def play_audio(client, message):
    if len(message.command) < 2:
        return await message.reply("Enna song venum macha?")

    query = " ".join(message.command[1:])
    m = await message.reply("🔎 Searching Audio via API...")

    video_id, title = youtube_search(query)
    if not video_id:
        return await m.edit("❌ YouTube API-la song kidaikala!")

    link = f"https://www.youtube.com/watch?v={video_id}"

    try:
        with YoutubeDL(ytdl_audio_opts) as ytdl:
            info = ytdl.extract_info(link, download=False)
            url = info['url']
        
        await m.edit(f"🎶 **Playing Audio:** [{title}]({link})", disable_web_page_preview=True, reply_markup=START_BUTTONS)
        await call_py.join_group_call(message.chat.id, AudioPiped(url))
    except Exception as e:
        logger.error(f"Play Error: {e}")
        await bot.send_message(LOGGER_GROUP, f"❌ **Play Error:**\n`{e}`")
        await m.edit("❌ Streaming-la error! Logs check pannu.")

# --- VIDEO PLAY (/vplay) ---
@bot.on_message(filters.command("vplay") & filters.group)
async def play_video(client, message):
    if len(message.command) < 2:
        return await message.reply("Enna video venum macha?")

    query = " ".join(message.command[1:])
    m = await message.reply("🎥 Searching Video via API...")

    video_id, title = youtube_search(query)
    if not video_id:
        return await m.edit("❌ YouTube API-la video kidaikala!")

    link = f"https://www.youtube.com/watch?v={video_id}"

    try:
        with YoutubeDL(ytdl_video_opts) as ytdl:
            info = ytdl.extract_info(link, download=False)
            url = info['url']
        
        await m.edit(f"🎬 **Streaming Video:** [{title}]({link})", disable_web_page_preview=True, reply_markup=START_BUTTONS)
        await call_py.join_group_call(message.chat.id, AudioVideoPiped(url))
    except Exception as e:
        logger.error(f"VPlay Error: {e}")
        await bot.send_message(LOGGER_GROUP, f"❌ **VPlay Error:**\n`{e}`")
        await m.edit("❌ Video Streaming-la error!")

# --- CONTROLS ---
@bot.on_message(filters.command(["vstop", "stop"]) & filters.group)
async def vstop_command(client, message):
    try:
        await call_py.leave_group_call(message.chat.id)
        await message.reply("👋 Stopped and Left VC!")
    except:
        pass

@bot.on_message(filters.command(["vpause", "pause"]) & filters.group)
async def vpause_command(client, message):
    try:
        await call_py.pause_stream(message.chat.id)
        await message.reply("⏸ Paused.")
    except:
        pass

@bot.on_message(filters.command(["vresume", "resume"]) & filters.group)
async def vresume_command(client, message):
    try:
        await call_py.resume_stream(message.chat.id)
        await message.reply("▶️ Resumed.")
    except:
        pass

# --- STARTUP ---
async def start_bot():
    await bot.start()
    await user.start()
    await call_py.start()
    print("✅ Bot & Userbot are Live with YouTube API!")
    await asyncio.Event().wait()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_bot())

