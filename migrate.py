"""
Migration Script - Upload downloads/ folder files to Telegram Channel + Save to MongoDB
Uses a userbot (string session) instead of a bot token.

Usage: python migrate.py
Edit the CONFIG section below, or set these as environment variables / .env values.
"""
import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv
from pyrogram import Client
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv()

# ─── CONFIG ──────────────────────────────────────────────────────────────
DOWNLOADS_DIR   = os.environ.get("DOWNLOADS_DIR", "/root/AnonXMusic/downloads")
MONGO_URI       = os.environ["MONGO_URI"]
DB_NAME         = os.environ.get("DB_NAME", "musicbot")
COLLECTION      = os.environ.get("COLLECTION", "songs")
API_ID          = int(os.environ["API_ID"])
API_HASH        = os.environ["API_HASH"]
SESSION_STRING  = os.environ["SESSION_STRING_1"]  # uses your first userbot account
CHANNEL_ID      = int(os.environ["CHANNEL_ID"])
# ───────────────────────────────────────────────────────────────────────


async def main():
    mongo = AsyncIOMotorClient(MONGO_URI)
    col = mongo[DB_NAME][COLLECTION]

    userbot = Client(
        "migrate_session",
        api_id=API_ID,
        api_hash=API_HASH,
        session_string=SESSION_STRING,
        in_memory=True,
    )
    await userbot.start()
    print("✅  Userbot connected")

    downloads = Path(DOWNLOADS_DIR)
    all_files = [f for f in downloads.iterdir() if f.is_file() and f.suffix in (".mp3", ".mp4", ".webm", ".m4a")]
    total = len(all_files)
    print(f"📁 Total files found: {total}")

    done = skipped = uploaded = failed = 0

    for file in all_files:
        done += 1
        video_id = file.stem
        file_type = file.suffix[1:]
        is_video = file_type == "mp4"
        field = "v" if is_video else "a"

        doc = await col.find_one({"_id": video_id})
        if doc and doc.get(field) is not None:
            print(f"[{done}/{total}] ⏭ Skip (already in DB): {file.name}")
            skipped += 1
            continue

        try:
            if is_video:
                sent = await userbot.send_video(chat_id=CHANNEL_ID, video=str(file), caption=video_id)
            else:
                sent = await userbot.send_audio(chat_id=CHANNEL_ID, audio=str(file), caption=video_id)

            await col.update_one({"_id": video_id}, {"$set": {field: sent.id}}, upsert=True)
            uploaded += 1
            print(f"[{done}/{total}] ✅  Uploaded: {file.name} → msg_id: {sent.id}")
        except Exception as ex:
            failed += 1
            print(f"[{done}/{total}] ❌  Failed: {file.name} → {ex}")

        await asyncio.sleep(0.5)

    await userbot.stop()
    mongo.close()

    print("\n" + "=" * 50)
    print("✅  COMPLETED")
    print(f"   Total files : {total}")
    print(f"   Uploaded    : {uploaded}")
    print(f"   Skipped     : {skipped}")
    print(f"   Failed      : {failed}")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
