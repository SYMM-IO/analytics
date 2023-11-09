import asyncio
import datetime

from pyrogram import Client

from app.models import StatsBotMessage
from config.local_settings import telegram_client_api_hash, telegram_client_api_id, stat_chat_id


def store_message(msg):
    messages = StatsBotMessage.select().order_by(StatsBotMessage.id.desc()).limit(1).execute()
    last_msg = None
    if len(messages) > 0:
        last_msg = messages[0]
        if last_msg.message_id == msg.id:
            return
    try:
        StatsBotMessage.create(timestamp=datetime.datetime.utcnow(), content=msg.text, message_id=msg.id)
        if last_msg:
            StatsBotMessage.delete_by_id(last_msg.id)
    except Exception as ex:
        print(ex)  # To not mess up thread


async def do_load_stats_messages(user_client):
    await user_client.start()
    async for msg in user_client.get_chat_history(stat_chat_id, 1):
        store_message(msg)
    await user_client.stop()


def load_stats_messages():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        user_client = Client('user_client', telegram_client_api_id, telegram_client_api_hash, hide_password=True)
        loop.run_until_complete(do_load_stats_messages(user_client))
    finally:
        loop.close()
