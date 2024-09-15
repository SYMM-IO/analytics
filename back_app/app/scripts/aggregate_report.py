from datetime import datetime, timedelta

from pandas import DataFrame
from sqlalchemy import select, func

from app import db_session
from app.models import Quote, Account

DEC18 = 10 ** 18
columns = """wallet
summation
last_day
count
""".split()
result = dict()
with db_session() as session:
    dt = datetime.now()
    res = session.execute(
        select(Account.user_id,
               func.sum((Quote.initialOpenedPrice * Quote.quantity) / (DEC18 * DEC18)),
               dt - func.max(Quote.timestamp),
               func.count(Quote.id),
               ).join(Account).group_by(Account.user_id)
    ).all()
    for i in res:
        v = result.setdefault(i[0].split('_')[-1], [0, timedelta(weeks=100000), 0])
        v[0] += i[1] or 0
        v[1] = min(v[1], i[2])
        v[2] += i[3]
df_dict = {k: [] for k in columns}
for k, v in result.items():
    df_dict[columns[0]].append(k)
    for i, c in enumerate(columns[1:]):
        df_dict[c].append(v[i])
main_df = DataFrame(df_dict)
main_df.to_csv('aggregate_report.csv', index=False)
