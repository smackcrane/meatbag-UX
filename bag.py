#!/usr/bin/python3

import yaml
import sys
import os
import pandas as pd
import json
import datetime
import readline
from tab_completer import tab_completer

script_path = os.path.dirname(os.path.realpath(__file__))

help_text = f"""meatbag_ux

bag <survey_name>
- begins prompting for answers to questions defined in {script_path}/surveys/<survey_name>.yaml
- saves responses as a row in {script_path}/data/<survey_name>.yaml
"""

arg_iter = iter(sys.argv[1:])
spec = None
for arg in arg_iter:
    if arg == '-h' or arg == '--help':
        print(help_text)
        sys.exit(0)
    if spec is None and os.path.exists(f'{script_path}/surveys/{arg}.yaml'):
        data_path = f'{script_path}/data/{arg}.csv'
        try:
            data = pd.read_csv(data_path, na_values=[], keep_default_na=False)
        except FileNotFoundError:
            data = None
        with open(f'{script_path}/surveys/{arg}.yaml', 'r') as f:
            spec = yaml.load(f, Loader=yaml.SafeLoader)
    else:
        raise Exception(f'Argument {arg} not supported or survey not found')

#print(spec)

# No argument given
if spec is None:
    print(help_text)
    sys.exit(0)

# initialize data frame if absent
if data is None:
    empty_data = {k:[] for k in spec['questions'].keys()}
    data = pd.DataFrame(empty_data)
# check if there are new questions
for q in spec['questions'].keys():
    if q not in data:
        data[q] = ['' for _ in range(data.shape[0])]
# check if there are date/time columns
for q in ['date', 'time']:
    if q not in data:
        data[q] = [None for _ in range(data.shape[0])]

# iterate through questions
questions = spec['questions'].items()

# turn on tab completion
readline.parse_and_bind("tab: complete")

# check if survey is marked as daily and already has some entries
replace_data = False
today = data.loc[data['date']==datetime.date.today().isoformat()]
if 'daily' in spec.keys() and not today.empty:
    replace_data = True
    [idx] = today.index.values
    today = today.iloc[0]
    row = today.to_dict()
else:
    row = {}

for name,question in questions:
    print(question['query'])

    # list past answers as options
    if '__past__' in question.get('options', ''):
        options = data[name].iloc[::-1].unique()
        print('  (' + ' | '.join(options) + ')')
    # or past words
    elif '__past_words__' in question.get('options', ''):
        options = data[name].iloc[::-1]
        options = ' '.join(options).split()
        options = pd.unique(options)
        print('  (' + ' | '.join(options) + ')')
    # or specified options
    else:
        options = question.get('options', [])
        if options:
            print('  (' + ' | '.join(options) + ')')

    # structured input
    if 'key-value' in question:
        response = {}
        # get past keys and values
        past_dicts = [json.loads(s) for s in data[name] if s]
        past_df = pd.DataFrame(past_dicts)
        keys = past_df.columns
        key_completer = tab_completer(keys)
        readline.set_completer(key_completer)
        key = input('key: > ')
        while key != 'q':
            value_completer = tab_completer(past_df.get(key, []))
            readline.set_completer(value_completer)
            value = input('value: > ')
            if value != 'q':
                response[key] = value
            readline.set_completer(key_completer)
            key = input('key: > ')
        response = json.dumps(response)
    # single input
    else:
        # set tab completion function
        completer = tab_completer(options)
        readline.set_completer(completer)
        # autofill with previous answer if any
        fill = str(row.get(name, ''))
        if fill:
            readline.set_startup_hook(lambda: readline.insert_text(fill))
        # read response
        response = input("> ")
        # reset autofill
        readline.set_startup_hook()
    row[name] = response

# autogen date/time cols
row['date'] = datetime.date.today().isoformat()
row['time'] = datetime.datetime.now().time().isoformat(timespec='minutes')

if replace_data:
    data.drop(idx, axis=0, inplace=True)
data = data.append(row, ignore_index=True)
data.to_csv(data_path, index=False)
