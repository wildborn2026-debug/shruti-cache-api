# Music Cache API

Drop-in replacement for the Shruti API, with your own MongoDB + Telegram
channel cache in front of it. Same `/download?url=...&type=...&api_key=...`
shape, so your bot needs almost no changes.

## How it works

```
Bot calls /download?url=<video_id>&type=audio&api_key=...
        │
        ▼
1. Check MongoDB (musicbot.songs) for this video_id
        │
   ┌────┴────┐
  FOUND     NOT FOUND
   │            │
   ▼            ▼
Download    Call Shruti API (their yt-dlp does the work,
from your   not yours — avoids IP-ban risk on your VPS)
Telegram        │
channel         ▼
(userbot)   Return bytes to bot IMMEDIATELY
   │            │
   ▼            ▼ (background task, doesn't block the response)
Return     Upload to channel + save msg_id to MongoDB
bytes      so next time it's instant for any bot, any VPS
```

If you've configured 1, 2, or 3 userbot accounts, every channel
download/upload automatically retries on the next account if one hits
a Telegram FloodWait — no code changes needed, it just uses however
many accounts you put in `.env`.

## Setup

### 1. Install dependencies

```bash
cd shruti-cache-api
pip install -r requirements.txt --break-system-packages
```

### 2. Configure `.env`

```bash
cp .env.example .env
nano .env
```

Fill in:
- `API_KEY` — make up a long random string, this is what your bots will use to call this API
- `MONGO_URI` — your MongoDB connection string (rotate the password since the old one was shared in chat)
- `CHANNEL_ID` — your existing `-1002675957297` channel
- `API_ID` / `API_HASH` — from my.telegram.org
- `SESSION_STRING_1` (and `_2`, `_3` if you have them) — your userbot session strings

### 3. Run it

```bash
# Quick test
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# Production (background, survives SSH disconnect)
pip install pm2 -g 2>/dev/null || true
pm2 start "python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000" --name music-api
pm2 save
```

### 4. Test it

```bash
curl "http://localhost:8000/health"

curl -v "http://localhost:8000/download?url=dQw4w9WgXcQ&type=audio&api_key=YOUR_API_KEY" --output /tmp/test.audio
```

## Point your bots at it

In each bot's `.env` (the `anony/core/youtube.py` file already reads these):

```env
SHRUTI_API_URL=http://YOUR_VPS_IP:8000
SHRUTI_API_KEY=YOUR_API_KEY
```

No domain needed — IP:port works identically for private bot-to-bot traffic.

## Migrating existing downloads/ folders

If you still have old `downloads/` folders on other bot VPS's with files
not yet in the channel, use `migrate.py` (uses a userbot, not a bot token):

```bash
DOWNLOADS_DIR=/root/AnonXMusic/downloads python3 migrate.py
```

It reads the same `.env`, so make sure `MONGO_URI`, `API_ID`, `API_HASH`,
`SESSION_STRING_1`, and `CHANNEL_ID` are set.

## Security notes

- **Rotate your bot token** (`@BotFather` → `/mybots` → Revoke) since it was
  shared in plaintext earlier — the userbot setup here doesn't use it anymore anyway.
- Keep `.env` out of git (`.gitignore` already covers it if you copy this into
  your existing repo).
- `API_KEY` is the only thing standing between your API and anyone who finds
  the IP — keep it long and random.
