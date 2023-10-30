import time
from collections import defaultdict

from config.local_settings import mention_cooldown, mention_for_red_alert_accounts


class IndicatorMode:
    RED = '🔴'
    YELLOW = '🟡'
    GREEN = '🟢'


class StateIndicator:
    last_mention_timestamps = defaultdict(lambda: 0)

    def __init__(self, name):
        self.name = name
        self.mode = None

    def set_mode(self, mode: IndicatorMode):
        self.mode = mode

    def get_mentions(self):
        if self.mode == IndicatorMode.RED:
            now = time.time()
            if now > StateIndicator.last_mention_timestamps[self.name] + mention_cooldown:
                StateIndicator.last_mention_timestamps[self.name] = now
                return mention_for_red_alert_accounts
        return []