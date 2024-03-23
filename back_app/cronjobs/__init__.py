import asyncio
import datetime

from pyrogram import Client

from config.local_settings import (
    telegram_client_api_id,
    telegram_client_api_hash,
    telegram_phone_number,
)
from config.settings import Context


def store_message(context: Context, msg):
    from app.models import StatsBotMessage

    messages = StatsBotMessage.select().where(StatsBotMessage.tenant == context.tenant).order_by(StatsBotMessage.id.desc()).limit(1).execute()
    last_msg = None
    if len(messages) > 0:
        last_msg = messages[0]
        if last_msg.message_id == msg.id:
            return
    try:
        StatsBotMessage.create(
            timestamp=datetime.datetime.utcnow(),
            content=msg.text,
            message_id=msg.id,
            tenant=context.tenant,
        )
        if last_msg:
            StatsBotMessage.delete_by_id(last_msg.id)
    except Exception as ex:
        print(ex)  # To not mess up thread


async def load_stats_messages(context: Context, user_client: Client):
    print(f"{context.tenant}: Loading stats messages")
    async for msg in user_client.get_chat_history(context.telegram_stat_group_id, 1):
        store_message(context, msg)


def load_stats_messages_sync(context: Context, user_client: Client, eventloop: asyncio.BaseEventLoop):
    eventloop.create_task(load_stats_messages(context, user_client))


async def setup_telegram_client():
    user_client = Client(
        "user_client",
        telegram_client_api_id,
        telegram_client_api_hash,
        hide_password=True,
        phone_number=telegram_phone_number,
    )
    return user_client
