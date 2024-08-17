import os

import requests

from config.local_settings import telegram_alert_group_id, telegram_bot_token, LOG_PATH
from config.settings import Context


def escape_markdown_v1(text):
    escape_chars = "_*[]~`"
    for char in escape_chars:
        text = text.replace(char, "\\" + char)
    return text


def _send_message(msg: str, group_id, retrying):
    for _ in range(retrying):
        url = f"https://api.telegram.org/bot{telegram_bot_token}/sendMessage"
        data = {
            "chat_id": group_id,
            "text": msg,
            "disable_web_page_preview": True,
            "parse_mode": "Markdown",
        }
        resp_msg = requests.post(url=url, data=data, timeout=5)
        if resp_msg.status_code == 200:
            break
        else:
            print(resp_msg.json())
    with open(LOG_PATH + f'/log_file_{os.environ["TENANT"]}.log', 'rb') as f:
        for _ in range(retrying):
            url = f"https://api.telegram.org/bot{telegram_bot_token}/sendDocument"
            data = {"chat_id": group_id}
            file = {'document': f}
            resp_doc = requests.post(url=url, data=data, files=file, timeout=5)
            if resp_doc.status_code == 200:
                break
            else:
                print(resp_doc.json())


def send_message(configuration: Context, msg: str, retrying=5):
    _send_message(msg, configuration.telegram_group_id, retrying)


def send_alert(msg: str, retrying=5):
    _send_message(msg, telegram_alert_group_id, retrying)
