from os import listdir

from dateutil import parser
from pandas import read_csv
from sqlalchemy import select, and_

from app import db_session
from app.models import BinanceIncome

directory_path = 'app/scripts/binance_archive_history'
with db_session() as session:
    for file_name in listdir(directory_path):
        tenant, hedger, _ = file_name.split('-')
        binance_incomes = session.scalars(
            select(BinanceIncome).where(
                and_(
                    BinanceIncome.tenant == tenant,
                    BinanceIncome.hedger == hedger,
                    )
            )
        ).all()
        operation_income_type = {
            'Transfer Between Spot Account and UM Futures Account': 'TRANSFER',
            'Transfer Between Sub-Account UM Futures and Spot Account': 'TRANSFER',
            'Futures Sub-account Internal Transfer': 'INTERNAL_TRANSFER',
            'Funding Fee': 'FUNDING_FEE',
        }

        df = read_csv(directory_path + '/' + file_name)
        df['Operation'] = df['Operation'].map(operation_income_type)
        df = df[(df['Operation'].isin(set(operation_income_type.values()))) & (df['Coin'] == 'USDT')]

        for timestamp, income_type, amount in zip(df['UTC_Time'], df['Operation'], df['Change']):
            rec = BinanceIncome(
                tenant=tenant,
                asset='USDT',
                amount=amount,
                type=income_type,
                hedger=hedger,
                timestamp=parser.parse(timestamp)
            )
            if rec not in binance_incomes:
                rec.save(session)
    session.commit()
