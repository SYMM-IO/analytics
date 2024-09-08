import requests
from pandas import DataFrame

from config.contexts.arbitrum_8_2 import arbitrum_8_2_contexts
from config.contexts.base_8_2 import base_8_2_contexts
from config.contexts.blast_8_2 import blast_8_2_contexts
from config.contexts.bnb_8_2 import bnb_8_2_contexts
from config.contexts.mantle_8_2 import mantle_8_2_contexts

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
fees_liquidation
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
pl_usdGross_unrealized
pl_usd_withFunding
pl_pct_withFunding
cva
partyAmm
lf
blockNum
tx
accountSource
""".split()
contexts = dict(arbitrum=arbitrum_8_2_contexts, base=base_8_2_contexts, blast=blast_8_2_contexts, bnb=bnb_8_2_contexts,
                mantle=mantle_8_2_contexts)
affiliates = dict()
for context in contexts.values():
    for affiliate in context.affiliates:
        affiliates[affiliate.symmio_multi_account] = affiliate.name
print('fetching accounts')
accounts = dict()
for chain in contexts:
    print(chain)
    timestamp = 0
    data_len = 1000
    while data_len == 1000:
        subgraph_query = {"query": """query MyQuery {
  accounts(first: 1000, orderBy: timestamp, where: {"""
                                   f'timestamp_gte: "{timestamp}"'
                                   """}) {
                                     accountSource
                                     id
                                     timestamp
                                   }
                                 }"""}
        response = requests.post(contexts[chain].subgraph_endpoint, json=subgraph_query)
        if response := response.json():
            if ("data" in response) and (data_len := len(response['data']['accounts'])):
                for acc in response['data']['accounts']:
                    accounts[acc['id']] = acc['accountSource']
        timestamp = response['data']['accounts'][-1]['timestamp']
        print(timestamp)
print('accounts fetched')
print('fetching quotes:')
for chain in contexts:
    print(chain)
    main_df = DataFrame({k: [] for k in columns})
    quote_id = 0
    data_len = 1000
    while data_len == 1000:
        df_dict = {k: [] for k in columns}
        subgraph_query = {"query": """query MyQuery {
          quotes(first: 1000, where: {"""
                                   f'quoteId_gt: "{quote_id}"'
                                   """}, orderBy: quoteId) {
                                     quoteStatus
                                     quoteId
                                     symbol
                                     eventsTimestamp {
                                       OpenPosition
                                       SendQuote
                                       LiquidatePositionsPartyA
                                       FillCloseRequest
                                     }
                                     blockNumber
                                     initialData {
                                       cva
                                       lf
                                       partyA
                                       partyAmm
                                       positionType
                                       marketPrice
                                     }
                                     userPaidFunding
                                     tradingFee
                                     openedPrice
                                     initialOpenedPrice
                                     transactionsHash {
                                       SendQuote
                                     }
                                     closedAmount
                                     quantity
                                     orderTypeOpen
                                     averageClosedPrice
                                   }
                                 }"""}
        response = requests.post(contexts[chain].subgraph_endpoint, json=subgraph_query)
        if response := response.json():
            if ("data" in response) and (data_len := len(response['data']['quotes'])):
                for quote in response['data']['quotes']:
                    if (int(quote['quoteStatus']) in [7, 8]) and accounts[quote['initialData']['partyA']]:
                        df_dict['chain'].append(chain)
                        df_dict['price_open'].append(int(quote['initialOpenedPrice']) / DEC18)
                        df_dict['price_close'].append(int(quote['averageClosedPrice']) / DEC18)
                        df_dict['blockNum'].append(quote['blockNumber'])
                        df_dict['quant_closed'].append(int(quote['closedAmount']) / DEC18)
                        df_dict['quant_open'].append(int(quote['quantity']) / DEC18)
                        df_dict['symbol'].append(quote['symbol'])
                        df_dict['quoteId'].append(quote['quoteId'])
                        df_dict['quoteStatus'].append(quote['quoteStatus'])
                        df_dict['partyAmm'].append(int(quote['initialData']['partyAmm']) / DEC18)
                        df_dict['position_orderType'].append('limit' if int(quote['orderTypeOpen']) == 0 else 'market')
                        df_dict['tx'].append(quote['transactionsHash']['SendQuote'])
                        df_dict['lf'].append(int(quote['initialData']['lf']) / DEC18)
                        df_dict['cva'].append(int(quote['initialData']['cva']) / DEC18)
                        df_dict['price_market'].append(int(quote['initialData']['marketPrice']) / DEC18)
                        df_dict['acct'].append(quote['initialData']['partyA'])
                        df_dict['accountSource'].append(accounts[quote['initialData']['partyA']])
                        df_dict['frontEnd'].append(affiliates[accounts[quote['initialData']['partyA']]])
                        df_dict['position_direction'].append(
                            'long' if int(quote['initialData']['positionType']) == 0 else 'short')
                        df_dict['time_open'].append(quote['eventsTimestamp']['OpenPosition'])
                        df_dict['time_closed'].append(quote['eventsTimestamp']['FillCloseRequest'])
                        if quote['eventsTimestamp']['FillCloseRequest'] and quote['eventsTimestamp']['OpenPosition']:
                            df_dict['time_heldInSeconds'].append(
                                int(quote['eventsTimestamp']['FillCloseRequest']) - int(
                                    quote['eventsTimestamp']['OpenPosition']))
                        else:
                            df_dict['time_heldInSeconds'].append(None)
                        df_dict['time_liquidated'].append(quote['eventsTimestamp']['LiquidatePositionsPartyA'])
                        df_dict['time_ordered'].append(quote['eventsTimestamp']['SendQuote'])
                        df_dict['time_updated'].append(None)
                        df_dict['fees_fundingRate'].append(quote['userPaidFunding'])
                        df_dict['fees_platform'].append(int(quote['userPaidFunding']) * int(quote['tradingFee']))
                        df_dict['fees_liquidation'].append(None)
                        df_dict['position_coll'].append((int(quote['initialData']['cva']) + int(
                            quote['initialData']['lf'])) / DEC18)
                        df_dict['position_size'].append(
                            (int(quote['initialOpenedPrice']) / DEC18) * (int(quote['quantity']) / DEC18))
                        df_dict['position_lev'].append(((int(quote['initialOpenedPrice']) * int(quote['quantity'])) / (
                                int(quote['initialData']['cva']) + int(quote['initialData']['lf']))) / DEC18)
                        df_dict['volume_open'].append(
                            (int(quote['initialOpenedPrice']) / DEC18) * (int(quote['quantity']) / DEC18))
                        df_dict['volume_close'].append(
                            (int(quote['averageClosedPrice']) / DEC18) * (int(quote['closedAmount']) / DEC18))
                        df_dict['price_openWithFunding'].append(int(quote['openedPrice']) / DEC18)
                        df_dict['chg_pct'].append(
                            100 * int(quote['initialOpenedPrice']) / int(quote['averageClosedPrice']))
                        df_dict['pl_usdGross_realized'].append(
                            (1 if int(quote['initialData']['positionType']) == 0 else -1) * ((int(
                                quote['averageClosedPrice']) - int(quote['initialOpenedPrice'])) / DEC18) * (
                                    int(quote['quantity']) / DEC18))
                        df_dict['pl_usd_withFunding'].append(None)
                        df_dict['pl_pct_withFunding'].append(None)
                quote_id = response['data']['quotes'][-1]['quoteId']
        main_df = main_df._append(DataFrame(df_dict))
        print(quote_id)
    main_df.to_csv(chain + '_quotes.csv', index=False)
