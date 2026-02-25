from aiogram import Bot
from aiogram.types import ChatMember
from database import get_channels


async def check_subscription(bot: Bot, user_id: int) -> tuple[bool, list]:
    """
    Returns (all_subscribed, unsubscribed_channels)
    """
    channels = await get_channels()
    if not channels:
        return True, []

    not_subscribed = []
    for ch in channels:
        try:
            member: ChatMember = await bot.get_chat_member(ch["channel_id"], user_id)
            if member.status in ("left", "kicked", "banned"):
                not_subscribed.append(ch)
        except Exception:
            not_subscribed.append(ch)

    return len(not_subscribed) == 0, not_subscribed
