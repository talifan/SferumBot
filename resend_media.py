"""Utility script to resend missed photo messages to Telegram."""

import asyncio
import os
from collections.abc import Iterable
from datetime import datetime, timezone

from aiohttp import ClientSession
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from dotenv import load_dotenv
from loguru import logger

from tg.methods import send_message
from vk.methods import get_history, get_user_credentials
from vk.vk_types import Message


def _parse_allowed_chats(raw_ids: str | None) -> list[int]:
    if not raw_ids:
        return []
    chunks: Iterable[str] = raw_ids.split(",")
    return [int(chunk.strip()) for chunk in chunks if chunk.strip()]


async def _resend_for_chat(
    session: ClientSession,
    bot: Bot,
    access_token: str,
    peer_id: int,
    tg_chat_id: int,
    tg_topic_id: int | None,
    date_threshold: int,
    count: int,
) -> int:
    history = await get_history(session, access_token, peer_id, count=count)
    profiles = history.get("profiles", [])

    chat_title = ""
    conversations = history.get("conversations", [])
    if conversations:
        chat_settings = conversations[0].get("chat_settings", {})
        chat_title = chat_settings.get("title", "")

    delivered = 0

    for item in reversed(history.get("items", [])):
        if item.get("date", 0) < date_threshold:
            continue

        msg = Message()
        await msg.async_init(
            session,
            **item,
            profiles=profiles,
            chat_title=chat_title,
        )

        if not any(kind == "photo" for kind, _ in msg.media):
            continue

        await send_message(bot, msg, tg_chat_id, tg_topic_id)
        delivered += 1

    return delivered


async def main() -> None:
    load_dotenv()

    AUTH_COOKIE = os.getenv("AUTH_COOKIE")
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    TG_CHAT_ID = os.getenv("TG_CHAT_ID") or os.getenv("TG_USER_ID")
    TG_TOPIC_ID = os.getenv("TG_TOPIC_ID")
    VK_CHAT_ID = os.getenv("VK_CHAT_ID")
    HISTORY_DEPTH = int(os.getenv("RESEND_HISTORY_DEPTH", "50"))

    if not all([AUTH_COOKIE, BOT_TOKEN, TG_CHAT_ID, VK_CHAT_ID]):
        raise RuntimeError("AUTH_COOKIE, BOT_TOKEN, TG_CHAT_ID and VK_CHAT_ID must be set")

    topic_id = int(TG_TOPIC_ID) if TG_TOPIC_ID else None
    tg_chat_id = int(TG_CHAT_ID)
    vk_peer_ids = _parse_allowed_chats(VK_CHAT_ID)

    if not vk_peer_ids:
        raise RuntimeError("VK_CHAT_ID must contain at least one peer id")

    logger.add("resend_media.log")
    logger.info("Starting manual resend for peers: {}", vk_peer_ids)

    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    threshold = int(today.timestamp())

    async with ClientSession() as session:
        user = await get_user_credentials(AUTH_COOKIE, session)
        access_token = user.access_token
        bot = Bot(
            BOT_TOKEN,
            default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN_V2),
        )

        total_sent = 0
        for peer in vk_peer_ids:
            total_sent += await _resend_for_chat(
                session,
                bot,
                access_token,
                peer,
                tg_chat_id,
                topic_id,
                threshold,
                HISTORY_DEPTH,
            )

        await bot.close()

    logger.info("Manual resend finished. Total photo messages sent: {}", total_sent)


if __name__ == "__main__":
    asyncio.run(main())
