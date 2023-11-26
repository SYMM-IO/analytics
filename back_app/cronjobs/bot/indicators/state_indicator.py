import time
from collections import defaultdict

from config.settings import Context


class IndicatorMode:
	RED = '🔴'
	YELLOW = '🟡'
	GREEN = '🟢'


class StateIndicator:
	last_mention_timestamps = defaultdict(lambda: 0)

	def __init__(self, name, mode=None):
		self.name = name
		self.mode = mode

	def set_mode(self, mode: IndicatorMode):
		self.mode = mode

	def get_applicable_mentions(self, context: Context):
		return context.mention_for_red_alert_accounts

	def get_mentions(self, context: Context):
		if self.mode == IndicatorMode.RED:
			now = time.time()
			if now > StateIndicator.last_mention_timestamps[self.name] + context.mention_cooldown:
				StateIndicator.last_mention_timestamps[self.name] = int(now)
				return self.get_applicable_mentions(context)
		return []
