import os
import re
import time
import logging
import tempfile
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp
from dotenv import load_dotenv

load_dotenv()

# ── Config ────────────────────────────────────────────────────────────────────
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not BOT_TOKEN:
    print("ERROR: Set TELEGRAM_BOT_TOKEN environment variable.")
    exit(1)

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
log = logging.getLogger(__name__)

# ── State ─────────────────────────────────────────────────────────────────────
START_TIME = time.time()
stats = {
    "downloads_attempted": 0,
    "downloads_succeeded": 0,
    "downloads_failed": 0,
}

# ── Helpers ───────────────────────────────────────────────────────────────────

def extract_url(text: str) -> str | None:
    """Pull the first URL out of a message."""
    match = re.search(r"https?://\S+", text or "")
    return match.group(0) if match else None


def is_facebook_url(url: str) -> bool:
    return any(d in url for d in ("facebook.com", "fb.watch", "fb.com"))


def download_facebook_video(url: str, output_dir: str) -> str:
    """Download video with yt-dlp and return the file path."""
    ydl_opts = {
        "format": "best[ext=mp4]/best",
        "outtmpl": os.path.join(output_dir, "%(title).40s.%(ext)s"),
        "merge_output_format": "mp4",
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info).replace(".webm", ".mp4").replace(".mkv", ".mp4")


def format_uptime(seconds: float) -> str:
    seconds = int(seconds)
    h, remainder = divmod(seconds, 3600)
    m, s = divmod(remainder, 60)
    parts = []
    if h:
        parts.append(f"{h}h")
    if m:
        parts.append(f"{m}m")
    parts.append(f"{s}s")
    return " ".join(parts)

# ── Handlers ──────────────────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Send me a Facebook video link and I'll download it for you.\n\n"
        "Supports public Facebook posts, Reels, and Watch videos."
    )


async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Pong!")


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uptime = format_uptime(time.time() - START_TIME)
    attempted = stats["downloads_attempted"]
    succeeded = stats["downloads_succeeded"]
    failed = stats["downloads_failed"]
    success_rate = f"{(succeeded / attempted * 100):.1f}%" if attempted > 0 else "N/A"

    await update.message.reply_text(
        f"🟢 Bot is online\n\n"
        f"⏱ Uptime: {uptime}\n"
        f"📥 Downloads attempted: {attempted}\n"
        f"✅ Succeeded: {succeeded}\n"
        f"❌ Failed: {failed}\n"
        f"📊 Success rate: {success_rate}"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = extract_url(update.message.text)

    if not url:
        await update.message.reply_text("Send me a Facebook video URL.")
        return

    if not is_facebook_url(url):
        await update.message.reply_text("That doesn't look like a Facebook URL. Please send a Facebook video link.")
        return

    status_msg = await update.message.reply_text("⬇️ Downloading...")
    stats["downloads_attempted"] += 1

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = download_facebook_video(url, tmpdir)

            size_mb = os.path.getsize(file_path) / (1024 * 1024)
            if size_mb > 50:
                stats["downloads_failed"] += 1
                await status_msg.edit_text(f"❌ File is {size_mb:.1f}MB — too large for Telegram (50MB limit).")
                return

            await status_msg.edit_text("📤 Uploading...")
            with open(file_path, "rb") as video_file:
                await update.message.reply_video(video=video_file, supports_streaming=True)

            stats["downloads_succeeded"] += 1
            await status_msg.delete()

    except yt_dlp.utils.DownloadError as e:
        log.error("Download error: %s", e)
        stats["downloads_failed"] += 1
        msg = str(e)
        if "Private" in msg or "login" in msg.lower():
            await status_msg.edit_text("❌ This video is private. Only public videos can be downloaded.")
        elif "404" in msg:
            await status_msg.edit_text("❌ Video not found. The link may be broken or removed.")
        else:
            await status_msg.edit_text("❌ Download failed. Make sure the video is public and try again.")

    except Exception as e:
        log.exception("Unexpected error")
        stats["downloads_failed"] += 1
        await status_msg.edit_text("❌ Something went wrong. Please try again.")

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ping", ping))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()