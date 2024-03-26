from pyrogram import Client
from sqlalchemy import select
from sqlalchemy.orm import Session

from config.local_settings import (
    telegram_client_api_id,
    telegram_client_api_hash,
    telegram_phone_number,
)
from config.settings import Context
from utils.parser_utils import parse_message

telegram_user_client: Client


async def start_telegram_client():
    global telegram_user_client
    telegram_user_client = Client(
        "user_client",
        telegram_client_api_id,
        telegram_client_api_hash,
        hide_password=True,
        phone_number=telegram_phone_number,
    )
    await telegram_user_client.start()


async def stop_telegram_client():
    await telegram_user_client.stop()


async def load_all_messages(context: Context):
    if not telegram_user_client.is_initialized or not telegram_user_client.is_connected:
        return
    from app import db_session

    with db_session() as session:
        await do_load_all_messages(session, context)


async def do_load_all_messages(session: Session, context: Context):
    from app.models import StatsBotMessage

    global telegram_user_client
    print(f"{context.tenant}: Loading all messages from the group")

    last_stored_message = session.scalar(
        select(StatsBotMessage).where(StatsBotMessage.tenant == context.tenant).order_by(StatsBotMessage.message_id.desc())
    )
    last_stored_message_id = last_stored_message.message_id if last_stored_message else 0
    print(f"{context.tenant}: Last loaded message id: {last_stored_message_id}")

    total_messages = 0
    async for msg in telegram_user_client.get_chat_history(context.telegram_stat_group_id, offset_id=last_stored_message_id):
        StatsBotMessage(
            timestamp=msg.date,
            content=parse_message(msg.text),
            message_id=msg.id,
            tenant=context.tenant,
        ).save(session)
        total_messages += 1
        print(f"\r{context.tenant}: Loaded {total_messages}", end="")

    print(f"Finished loading. Total messages processed: {total_messages}")
