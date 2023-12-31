from dataclasses import dataclass
from decimal import Decimal
from typing import List

from app.models import AffiliateSnapshot
from config.settings import Context
from cronjobs.bot.indicators.state_indicator import StateIndicator, IndicatorMode


@dataclass(frozen=True)
class FieldCheck:
    field_name_data: str
    field_name_stat_data: str
    threshold: float


class MismatchIndicator(StateIndicator):
    @staticmethod
    def percentage_difference(value1, value2):
        try:
            difference = abs(value1 - value2)
            average = (value1 + value2) / 2
            percentage_diff = (difference / average) * 100
            return percentage_diff
        except ZeroDivisionError:
            return "Error: Division by zero is not allowed."

    def update_state(
        self,
        data: AffiliateSnapshot,
        parsed_stat_bot_data: dict,
        field_checks: List[FieldCheck],
    ):
        for field_check in field_checks:
            value1 = getattr(data, field_check.field_name_data)

            is_method = callable(value1) and not isinstance(
                value1, (staticmethod, classmethod)
            )

            if is_method:
                value1 = value1()

            value2 = (
                Decimal(parsed_stat_bot_data[field_check.field_name_stat_data])
                * 10**18
            )
            diff = self.percentage_difference(value1, value2)
            if diff > field_check.threshold:
                self.set_mode(IndicatorMode.RED)
                return
        self.set_mode(IndicatorMode.GREEN)

    def get_applicable_mentions(self, context: Context):
        return context.mention_for_red_alert_maintenance_accounts
