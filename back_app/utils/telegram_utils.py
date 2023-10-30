import requests

from config.local_settings import telegram_group_id, telegram_bot_token, telegram_alert_group_id


def escape_markdown_v1(text):
    # Characters to escape for original Markdown (V1)
    escape_chars = '_*[]~`'
    for char in escape_chars:
        text = text.replace(char, '\\' + char)
    return text


def send_message(msg: str, retrying=5):
    for _ in range(retrying):
        url = f'https://api.telegram.org/bot{telegram_bot_token}/sendMessage'
        data = {
            'chat_id': telegram_group_id,
            'text': msg,
            'disable_web_page_preview': True,
            'parse_mode': 'Markdown',
        }
        resp = requests.post(url=url, data=data, timeout=5)
        if resp.status_code == 200:
            break
        else:
            print(resp.json())


def send_alert(msg: str, retrying=5):
    for _ in range(retrying):
        url = f'https://api.telegram.org/bot{telegram_bot_token}/sendMessage'
        data = {
            'chat_id': telegram_alert_group_id,
            'text': msg,
            'disable_web_page_preview': True,
            'parse_mode': 'Markdown',
        }
        resp = requests.post(url=url, data=data, timeout=5)
        if resp.status_code == 200:
            break
        else:
            print(resp.json())
