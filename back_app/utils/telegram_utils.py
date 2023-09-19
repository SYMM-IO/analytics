import requests

from config.local_settings import telegram_group_id, telegram_bot_token


def send_message(msg: str, retrying=5):
    for _ in range(retrying):
        url = f'https://api.telegram.org/bot{telegram_bot_token}/sendMessage'
        data = {
            'chat_id': telegram_group_id,
            'text': msg,
            'disable_web_page_preview': True
        }
        if requests.post(url=url, data=data, timeout=5).status_code == 200:
            break
