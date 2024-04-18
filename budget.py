#!/usr/bin/python3

import pandas as pd
import datetime
import config

money_bag = f'{config.path}/data/money.csv' # path to money survey
start_date = '2024-04-01' # ISO format---only take entries starting from this date

data = pd.read_csv(money_bag)
data = data.loc[data['date'] >= start_date]

income = data.loc[data['io'] == 'in', 'amount'].sum()
spent = data.loc[data['io'] == 'out', 'amount'].sum()
saved = data.loc[data['io'] == 'save', 'amount'].sum()

balance = income - spent - saved

color = '\033[31m' if balance < 0 else '\033[0m'
sign = '-' if balance < 0 else '+'

# pretty formatting for start date
d = datetime.date.fromisoformat(start_date)
d = d.strftime('%B ') + str(int(d.strftime('%d'))) + d.strftime(', %Y') # str(int( )) to remove potential leading 0 on day
print(f"""
Balanced budget from {d}

Income:  + ${income: 10.2f}
Spent:   - ${spent: 10.2f}
Saved:    (${saved: 10.2f})
---------------------------------
Balance: {color}{sign} ${abs(balance): 10.2f}\033[0m
""")

