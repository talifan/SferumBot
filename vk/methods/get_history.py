"""Fetch recent messages history."""

from aiohttp import ClientSession
from loguru import logger

from .consts import V


async def get_history(
    session: ClientSession,
    access_token: str,
    peer_id: int,
    count: int = 50,
) -> dict:
    """Return history block for the provided peer."""
    body = {
        "peer_id": peer_id,
        "count": count,
        "extended": 1,
        "fields": "id,first_name,last_name",
        "access_token": access_token,
    }

    query = {"v": V}

    async with session.post(
        "https://api.vk.me/method/messages.getHistory",
        data=body,
        params=query,
    ) as response:
        payload = await response.json()

    logger.debug("[VK API] get_history response: {}", payload)

    if payload.get("error"):
        raise RuntimeError(payload)

    return payload.get("response", {})
