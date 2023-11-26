import asyncio
import datetime

from pyrogram import Client

from app.models import StatsBotMessage
from config.local_settings import telegram_client_api_id, telegram_client_api_hash
from config.settings import Context


def store_message(context: Context, msg):
    messages = (
        StatsBotMessage.select()
        .where(StatsBotMessage.tenant == context.tenant)
        .order_by(StatsBotMessage.id.desc())
        .limit(1)
        .execute()
    )
    last_msg = None
    if len(messages) > 0:
        last_msg = messages[0]
        if last_msg.message_id == msg.id:
            return
    try:
        StatsBotMessage.create(
            timestamp=datetime.datetime.utcnow(), content=msg.text, message_id=msg.id, tenant=context.tenant
        )
        if last_msg:
            StatsBotMessage.delete_by_id(last_msg.id)
    except Exception as ex:
        print(ex)  # To not mess up thread


async def do_load_stats_messages(context: Context, user_client):
    await user_client.start()
    async for msg in user_client.get_chat_history(context.telegram_stat_group_id, 1):
        store_message(context, msg)
    await user_client.stop()


def load_stats_messages(context: Context):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    user_client = Client(
        f"user_client",
        telegram_client_api_id,
        telegram_client_api_hash,
        hide_password=True,
    )
    try:
        loop.run_until_complete(do_load_stats_messages(context, user_client))
    finally:
        loop.close()
