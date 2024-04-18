#!/usr/bin/python3
import pandas as pd
import os
import json
import config
from copy import deepcopy
import datetime
from dateutil.relativedelta import relativedelta

# read bills files
def load(filepath):
    with open(filepath, 'r') as f:
        d = json.load(f)
    return d

bills = [load(f'{config.autopay_path}/{file}') for file in os.listdir(config.autopay_path)]

# get moneybag since Apr 1 2024
data = pd.read_csv(f'{config.path}/data/money.csv')
data = data.loc[data['date'] >= '2024-04-01']

# find unpaid bills up to a month in the future
unpaid = []
for bill in bills:
    bill['date'] = datetime.date.fromisoformat(bill['date'])
    while bill['date'] <= datetime.date.today() + relativedelta(months=1):
        matches = data.loc[
                (data['description']==bill['description'])
                & (data['category']==bill['category'])
                & (data['subcategory']==bill['subcategory'])
                & (data['date']==bill['date'].isoformat())
                ]
        if matches.empty:
            unpaid.append(deepcopy(bill))
        bill['date'] += relativedelta(months=1)
# print a list of unpaid bills, amounts, due dates
unpaid = sorted(unpaid, key=lambda x : x['date'].isoformat()) # sort by due date
for i, bill in enumerate(unpaid):
    print(f'{i: 2d}:  {bill["description"].rjust(15)} {bill["date"].isoformat()}  ${bill["amount"].rjust(8)}')

# get input
try:
    i = int(input('Pay a bill? >  '))
    bill_to_pay = unpaid[i]
except ValueError:
    # no number (or non-number) entered, just exit
    raise SystemExit

# bag it
filepath = f'{config.autopay_path}/.tmp.autopay'
bill_to_pay['date'] = bill_to_pay['date'].isoformat()
with open(filepath, 'w') as f:
    json.dump(bill_to_pay, f)
os.system(f'bag money --editor --from-file {filepath}; rm {filepath}')

