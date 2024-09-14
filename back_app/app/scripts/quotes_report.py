from typing import List

from pandas import DataFrame
from sqlalchemy import select
from sqlalchemy.orm import load_only

from app import db_session
from app.models import Quote, Account, Symbol
from config.contexts.arbitrum_8_2 import arbitrum_8_2_contexts
from config.contexts.base_8_2 import base_8_2_contexts
from config.contexts.blast_8_2 import blast_8_2_contexts
from config.contexts.bnb_8_2 import bnb_8_2_contexts
from config.contexts.mantle_8_2 import mantle_8_2_contexts
from utils.model_utils import log_object_properties

DEC18 = 10 ** 18
columns = """chain
frontEnd
symbol
quoteId
acct
quoteStatus
time_ordered
time_open
time_updated
time_liquidated
time_closed
time_heldInSeconds
fees_fundingRate
fees_platform
position_coll
position_size
position_lev
position_direction
position_orderType
volume_open
volume_close
price_open
price_openWithFunding
price_close
price_market
quant_open
quant_closed
chg_pct
pl_usdGross_realized
pl_pct_withFunding
cva
partyAmm
lf
blockNum
accountSource
""".split()
contexts = dict(ARBITRUM_8_2=arbitrum_8_2_contexts, BASE_8_2=base_8_2_contexts, BLAST_8_2=blast_8_2_contexts,
                BNB_8_2=bnb_8_2_contexts, MANTLE_8_2=mantle_8_2_contexts)
affiliates = dict()
for context in contexts.values():
    for affiliate in context.affiliates:
        affiliates[affiliate.symmio_multi_account] = affiliate.name
accounts = dict()
for chain in contexts:
    timestamp = 0
    with db_session() as session:
        account: List[Account] = session.scalars(
            select(Account).options(
                load_only(
                    Account.accountSource,
                    Account.id,
                    Account.timestamp
                )))
        for acc in account:
            accounts[acc.id] = acc.accountSource
symbols = dict()
with db_session() as session:
    symbol: Symbol = session.scalars(
        select(Symbol).options(
            load_only(
                Symbol.name,
                Symbol.id,
            )))
    for _symbol in symbol:
        symbols[_symbol.id] = _symbol.name
quote_status = {7: 'CLOSED', 8: 'LIQUIDATED'}
for chain in contexts:
    print(chain)
    main_df = DataFrame({k: [] for k in columns})
    df_dict = {k: [] for k in columns}
    with db_session() as session:
        quotes: List[Quote] = session.scalars(
            select(Quote).where(Quote.tenant == chain).options(
                load_only(
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
                    Quote.partyB,
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
        try:
            for quote in quotes:
                if quote.quoteStatus in [7, 8] and accounts[quote.account_id]:
                    df_dict['chain'].append(chain)
                    df_dict['price_open'].append(quote.initialOpenedPrice / DEC18)
                    df_dict['price_close'].append(quote.averageClosedPrice / DEC18)
                    df_dict['blockNum'].append(quote.blockNumber)
                    df_dict['quant_closed'].append(quote.closedAmount / DEC18)
                    df_dict['quant_open'].append(quote.quantity / DEC18)
                    df_dict['symbol'].append(symbols[quote.symbol_id])
                    df_dict['quoteId'].append(quote.id)
                    df_dict['quoteStatus'].append(quote_status[quote.quoteStatus])
                    df_dict['partyAmm'].append(quote.initialPartyAmm / DEC18)
                    df_dict['position_orderType'].append('limit' if quote.orderTypeOpen == 0 else 'market')
                    df_dict['lf'].append(quote.initialLf / DEC18)
                    df_dict['cva'].append(quote.initialCva / DEC18)
                    df_dict['price_market'].append(quote.marketPrice / DEC18)
                    df_dict['acct'].append(quote.account_id)
                    df_dict['accountSource'].append(accounts[quote.account_id])
                    df_dict['frontEnd'].append(affiliates[accounts[quote.account_id]])
                    df_dict['position_direction'].append('long' if quote.positionType == 0 else 'short')
                    df_dict['time_open'].append(quote.timestampOpenPosition)
                    df_dict['time_closed'].append(quote.timestampFillCloseRequest)
                    if quote.timestampFillCloseRequest and quote.timestampOpenPosition:
                        df_dict['time_heldInSeconds'].append(
                            quote.timestampFillCloseRequest - quote.timestampOpenPosition)
                    else:
                        df_dict['time_heldInSeconds'].append(None)
                    df_dict['time_liquidated'].append(quote.timestampLiquidatePositionsPartyA)
                    df_dict['time_ordered'].append(quote.timestampSendQuote)
                    df_dict['time_updated'].append(quote.timestamp)
                    df_dict['fees_fundingRate'].append(quote.userPaidFunding)
                    df_dict['fees_platform'].append(
                        (quote.initialOpenedPrice / DEC18) * (quote.quantity / DEC18) * (quote.tradingFee / DEC18))
                    df_dict['position_coll'].append((quote.initialCva + quote.initialLf) / DEC18)
                    df_dict['position_size'].append((quote.initialOpenedPrice / DEC18) * (quote.quantity / DEC18))
                    df_dict['position_lev'].append(
                        ((quote.initialOpenedPrice * quote.quantity) / (quote.initialCva + quote.initialLf)) / DEC18)
                    df_dict['volume_open'].append((quote.initialOpenedPrice / DEC18) * (quote.quantity / DEC18))
                    df_dict['volume_close'].append((quote.averageClosedPrice / DEC18) * (quote.closedAmount / DEC18))
                    df_dict['price_openWithFunding'].append(quote.openedPrice / DEC18)
                    if quote.quoteStatus == 7:
                        df_dict['chg_pct'].append(100 * quote.initialOpenedPrice / quote.averageClosedPrice)
                    else:
                        df_dict['chg_pct'].append(100 * quote.initialOpenedPrice / quote.liquidatePrice)
                    pl_usdGross_realized = (1 if quote.positionType == 0 else -1) * (
                            (quote.averageClosedPrice - quote.initialOpenedPrice) / DEC18) * (
                                                   quote.quantity / DEC18) - quote.userPaidFunding - (
                                                   quote.initialOpenedPrice / DEC18) * (
                                                   quote.quantity / DEC18) * (quote.tradingFee / DEC18)
                    df_dict['pl_usdGross_realized'].append(pl_usdGross_realized)
                    df_dict['pl_pct_withFunding'].append(
                        100 * pl_usdGross_realized / (
                                (quote.initialLf + quote.initialCva + quote.initialPartyAmm) / DEC18))
        except Exception as e:
            print(log_object_properties(quote))
            print(e)
            continue
    main_df = main_df._append(DataFrame(df_dict))
    main_df.to_csv(chain + '_quotes.csv', index=False)
