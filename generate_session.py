"""
Helper to generate a Pyrogram session string for a userbot account.
Run this once per account (up to 3) and paste the output into .env
as SESSION_STRING_1 / SESSION_STRING_2 / SESSION_STRING_3.

Usage:
    python generate_session.py
"""
import asyncio
from pyrogram import Client

API_ID = int(input("API_ID: ").strip())
API_HASH = input("API_HASH: ").strip()


async def main():
    async with Client("session_gen", api_id=API_ID, api_hash=API_HASH, in_memory=True) as app:
        session_string = await app.export_session_string()
        print("\n" + "=" * 60)
        print("SESSION STRING (copy this into your .env file):")
        print("=" * 60)
        print(session_string)
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
