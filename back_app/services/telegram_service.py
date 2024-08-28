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
    tenant = os.environ.get("TENANT", False)
    if tenant:
        for _ in range(retrying):
            url = f"https://api.telegram.org/bot{telegram_bot_token}/sendDocument"

            with open(LOG_PATH + f"/log_file_{tenant}.log", "rb") as f:
                data = {"chat_id": group_id, "caption": msg, "parse_mode": "Markdown", "disable_web_page_preview": True}
                files = {"document": f}

                response = requests.post(url=url, data=data, files=files, timeout=5)
                if response.status_code == 200:
                    break
                else:
                    print(response.json())
        else:
            tenant = False

    if not tenant:
        for _ in range(retrying):
            url = f"https://api.telegram.org/bot{telegram_bot_token}/sendMessage"
            data = {
                "chat_id": group_id,
                "text": msg,
                "disable_web_page_preview": True,
                "parse_mode": "Markdown",
            }
            response = requests.post(url=url, data=data, timeout=5)
            if response.status_code == 200:
                break
            else:
                print(response.json())

    if response.status_code != 200:  # noqa
        print(f"Failed to send message after {retrying} attempts.")


def send_message(configuration: Context, msg: str, retrying=5):
    _send_message(msg, configuration.telegram_group_id, retrying)


def send_alert(msg: str, retrying=5):
    _send_message(msg, telegram_alert_group_id, retrying)
