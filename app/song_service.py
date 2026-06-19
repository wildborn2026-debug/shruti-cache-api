"""
Core orchestration logic:

  1. Check MongoDB for the video_id.
  2. If found -> download the cached copy from the channel and return it.
  3. If not found -> fetch from Shruti API, return those bytes immediately,
     and in the background upload to the channel + save to MongoDB so
     future requests (from any bot, any VPS) hit the fast cached path.
"""
import asyncio
import logging

from app import database, shruti_client, userbot_pool

logger = logging.getLogger("song_service")


async def get_song(video_id: str, video: bool = False) -> tuple[bytes, str] | None:
    """
    Returns (file_bytes, mime_type) for the caller to stream back, or None
    if the song could not be obtained from either the cache or Shruti.
    """
    field = "v" if video else "a"

    # 1. Check cache
    doc = await database.get_song(video_id)
    if doc and doc.get(field):
        msg_id = doc[field]
        result = await userbot_pool.download_from_channel(msg_id)
        if result:
            logger.info(f"{video_id}: served from channel cache (msg_id={msg_id})")
            return result
        # Cached msg_id was stale/deleted from channel - fall through to re-fetch
        logger.warning(f"{video_id}: cached msg_id {msg_id} could not be fetched, re-downloading.")

    # 2. Not cached (or cache was stale) -> fall back to Shruti API
    fetched = await shruti_client.fetch(video_id, video=video)
    if not fetched:
        return None

    file_bytes, mime, ext = fetched

    # Fire-and-forget: upload to channel + save to MongoDB in the background,
    # so this request doesn't wait on it. The bytes are already on their way
    # back to the caller.
    asyncio.create_task(_cache_in_background(video_id, file_bytes, ext, field, video))

    return file_bytes, mime


async def _cache_in_background(video_id: str, file_bytes: bytes, ext: str, field: str, is_video: bool):
    try:
        file_name = f"{video_id}.{ext}"
        msg_id = await userbot_pool.upload_to_channel(file_bytes, file_name, video_id, is_video)
        await database.save_msg_id(video_id, field, msg_id)
        logger.info(f"{video_id}: cached to channel (msg_id={msg_id}) and saved to MongoDB.")
    except Exception as ex:
        logger.warning(f"{video_id}: background caching failed: {ex}")
