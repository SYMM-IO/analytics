import json
from datetime import datetime, timedelta

import peewee

from app.models import AffiliateSnapshot, HedgerSnapshot
from config.settings import (
    fetch_data_interval,
)


def get_yesterday_last_affiliate_snapshot(affiliate_snapshot: AffiliateSnapshot):
    yesterday = datetime.utcnow() - timedelta(days=1)
    yesterday_end = datetime(yesterday.year, yesterday.month, yesterday.day, 23, 59, 59)

    try:
        return (
            AffiliateSnapshot.select()
            .where(
                AffiliateSnapshot.timestamp <= yesterday_end,
                AffiliateSnapshot.name == affiliate_snapshot.name,
            )
            .order_by(AffiliateSnapshot.timestamp.desc())
            .get()
        )
    except:  # FIXME is for the first time
        return (
            AffiliateSnapshot.select()
            .where(
                AffiliateSnapshot.name == affiliate_snapshot.name,
            )
            .order_by(AffiliateSnapshot.timestamp.desc())
            .get()
        )


def get_yesterday_last_hedger_snapshot(hedger_snapshot: HedgerSnapshot):
    yesterday = datetime.utcnow() - timedelta(days=1)
    yesterday_end = datetime(yesterday.year, yesterday.month, yesterday.day, 23, 59, 59)

    try:
        return (
            HedgerSnapshot.select()
            .where(
                HedgerSnapshot.timestamp <= yesterday_end,
                HedgerSnapshot.name == hedger_snapshot.name,
            )
            .order_by(HedgerSnapshot.timestamp.desc())
            .get()
        )
    except:  # FIXME is for the first time
        return (
            HedgerSnapshot.select()
            .where(
                HedgerSnapshot.name == hedger_snapshot.name,
            )
            .order_by(HedgerSnapshot.timestamp.desc())
            .get()
        )


def calculate_liquidator_states_diff(old_states, new_states):
    diff_states = []

    old_states_dict = {state["address"]: state for state in old_states}
    new_states_dict = {state["address"]: state for state in new_states}

    for address, new_state in new_states_dict.items():
        old_state = old_states_dict.get(address)
        if old_state:
            diff_state = {
                "address": address,
                "withdraw": new_state["withdraw"] - old_state["withdraw"],
                "balance": new_state["balance"] - old_state["balance"],
            }
        else:
            diff_state = new_state
        diff_states.append(diff_state)

    return diff_states


def calculate_status_quotes_diff(old_quotes, new_quotes):
    diff_quotes = {}

    for quote, new_value in new_quotes.items():
        old_value = old_quotes.get(quote)
        if old_value is not None:
            diff = new_value - old_value
        else:
            diff = new_value
        diff_quotes[quote] = diff

    return diff_quotes


def calculate_affiliates_snapshot_diff(
    old_data: AffiliateSnapshot, new_data: AffiliateSnapshot
):
    diff_data = AffiliateSnapshot()

    field_names = [
        field.name
        for field in AffiliateSnapshot._meta.fields.values()
        if isinstance(field, peewee.DecimalField)
        or isinstance(field, peewee.IntegerField)
    ]

    for field_name in field_names:
        old_value = getattr(old_data, field_name)
        new_value = getattr(new_data, field_name)
        diff = new_value - old_value
        setattr(diff_data, field_name, diff)

    diff_data.timestamp = new_data.timestamp

    diff_data.status_quotes = calculate_status_quotes_diff(
        json.loads(old_data.status_quotes.replace("'", '"')), new_data.status_quotes
    )
    diff_data.liquidator_states = calculate_liquidator_states_diff(
        old_data.liquidator_states, new_data.liquidator_states
    )

    return diff_data


def calculate_hedger_snapshot_diff(old_data: HedgerSnapshot, new_data: HedgerSnapshot):
    diff_data = HedgerSnapshot()

    field_names = [
        field.name
        for field in HedgerSnapshot._meta.fields.values()
        if isinstance(field, peewee.DecimalField)
        or isinstance(field, peewee.IntegerField)
    ]

    for field_name in field_names:
        old_value = getattr(old_data, field_name)
        new_value = getattr(new_data, field_name)
        diff = new_value - old_value
        setattr(diff_data, field_name, diff)

    diff_data.timestamp = new_data.timestamp

    return diff_data


def is_end_of_day():
    now = datetime.utcnow()
    end_of_day = datetime(
        now.year, now.month, now.day, 23, 59 - (fetch_data_interval // 60), 30
    )
    return now >= end_of_day
