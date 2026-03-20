# fbdl-bot

A Telegram bot that downloads public Facebook videos and delivers them directly in chat. Built with `python-telegram-bot` and `yt-dlp`.

## Features

- Detects Facebook URLs in any message (`facebook.com`, `fb.watch`, `fb.com`)
- Downloads public posts, Reels, and Watch videos
- Streams the video back to the user in Telegram
- Enforces Telegram's 50 MB upload limit with a clear error message
- Per-session download stats (attempts, successes, failures, uptime)

## Requirements

- Python 3.10+
- A Telegram Bot Token from [@BotFather](https://t.me/BotFather)

## Installation

```bash
git clone https://github.com/pawanhirumina/fb-downloader-tgbot.git
cd fbdl-bot
pip install python-telegram-bot yt-dlp python-dotenv
```

## Configuration

Create a `.env` file in the project root:

```env
TELEGRAM_BOT_TOKEN=your_token_here
```

The bot will exit immediately on startup if this variable is missing.

## Usage

```bash
python bot.py
```

The bot uses long-polling — no webhook or public server required.

Once running, send it any message containing a public Facebook video URL. It will reply with the downloaded video.

## Commands

| Command   | Description                                     |
| --------- | ----------------------------------------------- |
| `/start`  | Welcome message and usage instructions          |
| `/ping`   | Liveness check — replies with `Pong!`           |
| `/status` | Shows uptime, download counts, and success rate |

## How It Works

1. Incoming message is scanned for a URL with a simple regex
2. The URL is checked against known Facebook domains
3. `yt-dlp` downloads the best available MP4 to a temporary directory
4. File size is verified against the 50 MB Telegram limit
5. Video is uploaded via `reply_video` and the temp directory is cleaned up automatically

## Error Handling

| Scenario                        | Response                                                   |
| ------------------------------- | ---------------------------------------------------------- |
| No URL in message               | Prompts the user to send a Facebook link                   |
| Non-Facebook URL                | Tells the user only Facebook links are supported           |
| Private or login-required video | Explains the video is private                              |
| 404 / removed video             | Reports the link is broken or removed                      |
| File over 50 MB                 | Reports the file size and the Telegram limit               |
| Unexpected error                | Generic failure message; full traceback logged server-side |

## Project Structure

```
bot.py          # Entry point — all handlers, helpers, and bot setup
.env            # Bot token (not committed)
```

## Dependencies

| Package               | Purpose                                 |
| --------------------- | --------------------------------------- |
| `python-telegram-bot` | Async Telegram Bot API wrapper          |
| `yt-dlp`              | Video extraction and download           |
| `python-dotenv`       | Loads `.env` into environment variables |

## Notes

- Only **public** videos can be downloaded. Private videos, videos behind a login wall, or region-restricted content will fail with an appropriate error.
- Temporary files are written to a `tempfile.TemporaryDirectory` and deleted automatically after upload, regardless of success or failure.
- Stats reset on each bot restart — there is no persistent storage.

## License

MIT
