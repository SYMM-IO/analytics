import os
from datetime import datetime
from typing import List

from pandas import DataFrame
from sqlalchemy import select, func, and_
from sqlalchemy.orm import load_only

from src.app import db_session
from src.app.models import Quote, Account
from src.config.contexts.arbitrum_8_2 import arbitrum_8_2_contexts
from src.config.contexts.base_8_2 import base_8_2_contexts
from src.config.contexts.blast_8_2 import blast_8_2_contexts
from src.config.contexts.bnb_8_2 import bnb_8_2_contexts
from src.config.contexts.mantle_8_2 import mantle_8_2_contexts
from src.config.local_settings import REPORTS_PATH

if not os.path.exists(REPORTS_PATH):
    os.mkdir(REPORTS_PATH)

DEC18 = 10 ** 18
columns = ['Wallet', 'Total trade volume', 'Last interaction', 'Number of quotes']
contexts = dict(ARBITRUM_8_2=arbitrum_8_2_contexts, BASE_8_2=base_8_2_contexts, BLAST_8_2=blast_8_2_contexts,
                BNB_8_2=bnb_8_2_contexts, MANTLE_8_2=mantle_8_2_contexts)


def get_aggregate_report(start_date, end_date, selected_affiliate):
    affiliates = dict()
    for context in contexts.values():
        for affiliate in context.affiliates:
            if not selected_affiliate or selected_affiliate == affiliate.name:
                affiliates[affiliate.symmio_multi_account] = affiliate.name
    accounts = dict()
    with db_session() as session:
        account: List[Account] = session.scalars(
            select(Account).where(
                and_(
                    Account.timestamp <= end_date,
                    Account.timestamp >= start_date,
                )).options(
                load_only(
                    Account.accountSource,
                    Account.id,
                    Account.timestamp,
                )))
        for acc in account:
            accounts[acc.id] = acc.accountSource
    for affiliate in set(affiliates.values()):
        print(affiliate)
        valid_account_ids = [acc_id for acc_id, acc_src in accounts.items() if affiliates.get(acc_src) == affiliate]
        result = dict()
        with db_session() as session:
            res = session.execute(
                select(Account.user_id,
                       func.sum((Quote.initialOpenedPrice * Quote.quantity) / (DEC18 * DEC18)),
                       end_date - func.max(Quote.timestamp),
                       func.count(Quote.id),
                       ).where(
                    and_(
                        Quote.account_id.in_(valid_account_ids),
                        Quote.timestamp <= end_date,
                        Quote.timestamp >= start_date,
                    )).join(Account).group_by(Account.user_id)
            ).all()
            for user_id, total_trade_volume, last_interaction, number_of_quotes in res:
                wallet_address = user_id.split('_')[-1]
                val = result.setdefault(wallet_address, [0, end_date - datetime(1, 1, 1), 0])
                val[0] += total_trade_volume or 0
                val[1] = min(val[1], last_interaction)
                val[2] += number_of_quotes
        df_dict = {k: [] for k in columns}
        for k, v in result.items():
            df_dict[columns[0]].append(k)
            df_dict[columns[1]].append(v[0])
            df_dict[columns[2]].append(f'{v[1].days} days')
            df_dict[columns[3]].append(v[2])
        main_df = DataFrame(df_dict)
        main_df.to_csv(f'{REPORTS_PATH}/{affiliate}_aggregate.csv', index=False)
