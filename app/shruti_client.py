"""
Fallback client for the Shruti API. Used only when a song isn't found
in our own MongoDB cache yet. We never run yt-dlp ourselves here —
this avoids putting any download load (and IP-ban risk) on our own VPS.
"""
import logging

import aiohttp

from app import config

logger = logging.getLogger("shruti_client")


async def fetch(video_id: str, video: bool = False) -> tuple[bytes, str, str] | None:
    """
    Downloads a fresh copy from the Shruti API.
    Returns (file_bytes, mime_type, file_extension) or None on failure.
    """
    media_type = "video" if video else "audio"
    timeout = 600 if video else 300

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{config.SHRUTI_API_URL}/download",
                params={"url": video_id, "type": media_type, "api_key": config.SHRUTI_API_KEY},
                timeout=aiohttp.ClientTimeout(total=timeout),
            ) as resp:
                if resp.status != 200:
                    body = await resp.text()
                    logger.warning(f"Shruti API failed for {video_id}: HTTP {resp.status} | {body[:200]}")
                    return None

                data = await resp.read()
                if not data:
                    return None

                mime = resp.headers.get("content-type", "audio/webm" if not video else "video/mp4")
                ext = mime.split("/")[-1].split(";")[0] or ("webm" if not video else "mp4")
                return data, mime, ext

    except Exception as ex:
        logger.warning(f"Shruti API error for {video_id}: {ex}")
        return None
