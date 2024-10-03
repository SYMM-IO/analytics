import os
from datetime import datetime
from decimal import Decimal
from time import time
from typing import List

from pandas import DataFrame
from sqlalchemy import select, and_
from sqlalchemy.orm import load_only

from src.app import db_session
from src.app.models import Quote, Account, Symbol
from src.config.contexts.arbitrum_8_2 import arbitrum_8_2_contexts
from src.config.contexts.base_8_2 import base_8_2_contexts
from src.config.contexts.blast_8_2 import blast_8_2_contexts
from src.config.contexts.bnb_8_2 import bnb_8_2_contexts
from src.config.contexts.mantle_8_2 import mantle_8_2_contexts
from src.config.local_settings import REPORTS_PATH

if not os.path.exists(REPORTS_PATH):
    os.mkdir(REPORTS_PATH)

start_date = datetime.fromtimestamp(float(os.environ.get('start', 0)))
end_date = datetime.fromtimestamp(float(os.environ.get('end', time())))
selected_affiliate = os.environ.get('affiliate')

DEC18 = Decimal(10 ** 18)
columns = ['Chain', 'Symbol', 'Quote id', 'Account', 'Quote status', 'Ordered time', 'Open time',
           'Updated time', 'Liquidated time', 'Closed time', 'Open duration', 'Funding rate fees paid',
           'Platform fees paid', 'Locked collateral', 'Leverage', 'Direction', 'Order type', 'Open size', 'Close size',
           'Open price', 'Open price after funding', 'Close price', 'Market price', 'Open quantity', 'Close quantity',
           'Price change (%)', 'Profit', 'Return', 'CVA', 'PartyA MM', 'LF', 'Block number', 'Multi account']

contexts = dict(ARBITRUM_8_2=arbitrum_8_2_contexts, BASE_8_2=base_8_2_contexts, BLAST_8_2=blast_8_2_contexts,
                BNB_8_2=bnb_8_2_contexts, MANTLE_8_2=mantle_8_2_contexts)
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
symbols = dict()
with db_session() as session:
    symbol: List[Symbol] = session.scalars(
        select(Symbol).options(
            load_only(
                Symbol.name,
                Symbol.id,
            )))
    for _symbol in symbol:
        symbols[_symbol.id] = _symbol.name
quote_status = {0: 'PENDING', 1: 'LOCKED', 2: 'CANCEL_PENDING', 3: 'CANCELED', 4: 'OPENED', 5: 'CLOSE_PENDING',
                6: 'CANCEL_CLOSE_PENDING', 7: 'CLOSED', 8: 'LIQUIDATED', 9: 'EXPIRED', 10: 'LIQUIDATED_PENDING'}
for affiliate in set(affiliates.values()):
    print(affiliate)
    df_dict = {k: [] for k in columns}
    valid_account_ids = [acc_id for acc_id, acc_src in accounts.items() if affiliates.get(acc_src) == affiliate]
    with db_session() as session:
        quotes: List[Quote] = session.scalars(
            select(Quote).where(
                and_(
                    Quote.account_id.in_(valid_account_ids),
                    Quote.timestamp <= end_date,
                    Quote.timestampSendQuote >= start_date,
                )
            ).options(
                load_only(
                    Quote.tenant,
                    Quote.quoteStatus,
                    Quote.id,
                    Quote.symbol_id,
                    Quote.timestampOpenPosition,
                    Quote.timestampSendQuote,
                    Quote.timestampLiquidatePositionsPartyA,
                    Quote.timestampFillCloseRequest,
                    Quote.blockNumber,
                    Quote.initialCva,
                    Quote.initialLf,
                    Quote.account_id,
                    Quote.userPaidFunding,
                    Quote.tradingFee,
                    Quote.openedPrice,
                    Quote.initialOpenedPrice,
                    Quote.closedAmount,
                    Quote.quantity,
                    Quote.orderTypeOpen,
                    Quote.averageClosedPrice,
                    Quote.initialPartyAmm,
                    Quote.marketPrice,
                    Quote.positionType,
                    Quote.liquidatePrice,
                    Quote.timestamp,
                )))
        for quote in quotes:
            df_dict['Chain'].append(quote.tenant)
            df_dict['Symbol'].append(symbols[quote.symbol_id])
            df_dict['Quote id'].append(quote.id.split('_')[-1])
            df_dict['Account'].append(quote.account_id)
            df_dict['Quote status'].append(quote_status[quote.quoteStatus])
            df_dict['Ordered time'].append(quote.timestampSendQuote)
            df_dict['Open time'].append(quote.timestampOpenPosition)
            df_dict['Updated time'].append(quote.timestamp)
            df_dict['Liquidated time'].append(quote.timestampLiquidatePositionsPartyA)
            df_dict['Closed time'].append(quote.timestampFillCloseRequest)
            if quote.timestampFillCloseRequest and quote.timestampOpenPosition:
                df_dict['Open duration'].append(quote.timestampFillCloseRequest - quote.timestampOpenPosition)
            else:
                df_dict['Open duration'].append(None)
            df_dict['Funding rate fees paid'].append(Decimal(quote.userPaidFunding) / DEC18)
            df_dict['Platform fees paid'].append(
                (Decimal(quote.initialOpenedPrice or 0) / DEC18) * (Decimal(quote.quantity) / DEC18) * (
                        Decimal(quote.tradingFee) / DEC18))
            df_dict['Locked collateral'].append(Decimal(quote.initialCva + quote.initialLf) / DEC18)
            df_dict['Leverage'].append(
                ((Decimal(quote.initialOpenedPrice or 0) * Decimal(quote.quantity or 0)) / Decimal(
                    quote.initialCva + quote.initialLf)) / DEC18)
            df_dict['Direction'].append('long' if int(quote.positionType) == 0 else 'short')
            df_dict['Order type'].append('limit' if int(quote.orderTypeOpen) == 0 else 'market')
            df_dict['Open size'].append(
                (Decimal(quote.initialOpenedPrice or 0) / DEC18) * (Decimal(quote.quantity) / DEC18))
            df_dict['Close size'].append(
                (Decimal(quote.averageClosedPrice) / DEC18) * (Decimal(quote.closedAmount) / DEC18))
            df_dict['Open price'].append(Decimal(quote.initialOpenedPrice or 0) / DEC18)
            df_dict['Open price after funding'].append(Decimal(quote.openedPrice or 0) / DEC18)
            df_dict['Market price'].append(Decimal(quote.marketPrice) / DEC18)
            df_dict['Close price'].append(Decimal(quote.averageClosedPrice) / DEC18)
            df_dict['Open quantity'].append(Decimal(quote.quantity) / DEC18)
            df_dict['Close quantity'].append(Decimal(quote.closedAmount) / DEC18)
            if quote.quoteStatus == 7 and quote.averageClosedPrice:
                df_dict['Price change (%)'].append(
                    100 * (quote.averageClosedPrice - quote.initialOpenedPrice) / quote.initialOpenedPrice)
            elif quote.quoteStatus == 8 and quote.liquidatePrice:
                df_dict['Price change (%)'].append(
                    100 * (quote.liquidatePrice - quote.initialOpenedPrice) / quote.initialOpenedPrice)
            else:
                df_dict['Price change (%)'].append(None)
            pl_usdGross_realized = (1 if quote.positionType == 0 else -1) * (
                    (Decimal(quote.averageClosedPrice or 0) - Decimal(quote.initialOpenedPrice or 0)) / DEC18) * (
                                           Decimal(quote.quantity) / DEC18) - Decimal(quote.userPaidFunding) / DEC18 - (
                                           Decimal(quote.initialOpenedPrice or 0) / DEC18) * (
                                           Decimal(quote.quantity) / DEC18) * (Decimal(quote.tradingFee) / DEC18)
            df_dict['Profit'].append(pl_usdGross_realized)
            df_dict['Return'].append(
                100 * pl_usdGross_realized / (
                        Decimal(quote.initialLf + quote.initialCva + quote.initialPartyAmm) / DEC18))
            df_dict['CVA'].append(Decimal(quote.initialCva) / DEC18)
            df_dict['PartyA MM'].append(Decimal(quote.initialPartyAmm) / DEC18)
            df_dict['LF'].append(Decimal(quote.initialLf) / DEC18)
            df_dict['Block number'].append(quote.blockNumber)
            df_dict['Multi account'].append(accounts.get(quote.account_id))
    main_df = DataFrame(df_dict)
    main_df.to_csv(f'{REPORTS_PATH}/{affiliate}_quotes.csv', index=False)
