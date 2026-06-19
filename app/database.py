"""
MongoDB layer. Same schema as the existing migrate.py script:
    { "_id": "<video_id>", "a": <audio_msg_id>, "v": <video_msg_id> }
"""
from motor.motor_asyncio import AsyncIOMotorClient

from app import config

_client: AsyncIOMotorClient | None = None
_col = None


def connect():
    global _client, _col
    _client = AsyncIOMotorClient(config.MONGO_URI)
    _col = _client[config.DB_NAME][config.COLLECTION]


def close():
    if _client:
        _client.close()


async def get_song(video_id: str) -> dict | None:
    return await _col.find_one({"_id": video_id})


async def save_msg_id(video_id: str, field: str, msg_id: int):
    """field is 'a' for audio, 'v' for video."""
    await _col.update_one(
        {"_id": video_id},
        {"$set": {field: msg_id}},
        upsert=True,
    )
