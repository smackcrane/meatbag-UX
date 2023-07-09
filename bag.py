#!/usr/bin/python3

import yaml
import sys
import os
import pandas as pd
import json
import datetime
import readline
import re
from tab_completer import tab_completer
import argparse
import config


parser = argparse.ArgumentParser(
        prog='bag',
        description='fill out a user-defined survey and compile results in a csv file.',
)
parser.add_argument(
        dest='survey',
        metavar='survey_name',
        help=f'survey name, refers to survey defined in {config.path}/surveys/<survey_name>.yaml')
parser.add_argument(
        '-e', '--editor',
        action='store_true',
        help='opens the row in a text editor (set by environment var $EDITOR) rather than going through survey incrementally. Only written for Unix at the moment. Intended mainly for daily surveys.'
)
parser.add_argument(
        '-o', '--offset',
        action='store',
        type=int,
        default=0,
        help='date offset to record, in negative days; also used to look up and edit existing record for "daily" surveys; e.g. `bag -o1 foo` will record an entry for survey `foo` timestamed yesterday, or in case `foo` is a daily survey, will edit the entry from yesterday.'
)

args = parser.parse_args()

# load survey
survey_path = f'{config.path}/surveys/{args.survey}.yaml'
assert os.path.isfile(survey_path), f'survey not found at {survey_path}'
with open(survey_path, 'r') as f:
    spec = yaml.load(f, Loader=yaml.SafeLoader)

# load data
data_path = f'{config.path}/data/{args.survey}.csv'
try:
    data = pd.read_csv(data_path, na_values=[], keep_default_na=False)
except FileNotFoundError:
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
todays_date = datetime.date.today() + datetime.timedelta(days=-args.offset)
todays_date = todays_date.isoformat()
today = data.loc[data['date']==todays_date]
if 'daily' in spec.keys() and not today.empty:
    replace_data = True
    [idx] = today.index.values
    today = today.iloc[0]
    row = today.to_dict()
else:
    # initialize data row with keys only
    row = {q[0]: '' for q in questions}

# autogen date/time cols
row['date'] = todays_date
row['time'] = datetime.datetime.now().time().isoformat(timespec='minutes')


# Quick data input in text editor
if args.editor:
    # YAML is a hackier package and complains about numpy numeric types from pandas;
    #   also is more fiddly re: quotes
    EDITOR = os.getenv("EDITOR")
    with open('/tmp/bag','w') as f:
        json.dump(row,f,indent=4)
    os.system(f"{EDITOR} /tmp/bag")
    with open('/tmp/bag') as f:
        new_row = json.load(f)
    row = new_row
# Go through survey on command line
else:
    # manual loop to allow going backwards
    i = 0
    while i < len(questions):
        try:
            name, question = list(questions)[i]
            print(question['query'])

            # Look at top level of survey spec for a default option set
            option_spec = question.get('options', spec.get('default_options', ''))
            # check for __past_n__ option
            past_n = next(
                        filter(
                            lambda s: re.match(r'__past_\d+__', s),
                            option_spec),
                        None)
            # list past answers as options
            if '__past__' in option_spec:
                options = data[name].iloc[::-1].unique()
                print('  (' + ' | '.join(map(str, options)) + ')')
            # or answers from past n days
            elif past_n:
                # NB past_n = '__past_XX__' for some digits XX
                # so past_n.split('_') = ['', '', 'past', 'XX', '', '']
                n = int(past_n.split('_')[3])
                cutoff = datetime.date.today() - datetime.timedelta(days=n)
                past30 = data.loc[data['date'] > cutoff.isoformat()]
                options = past30[name].iloc[::-1].unique()
                print('  (' + ' | '.join(map(str, options)) + ')')
            # or past words
            elif '__past_words__' in option_spec:
                options = data[name].iloc[::-1]
                options = ' '.join(options).split()
                options = pd.unique(options)
                print('  (' + ' | '.join(map(str, options)) + ')')
            # or specified options
            elif len(option_spec) > 0:
                # ignore double underscored options
                options = [op for op in option_spec if '__' not in op]
                print('  (' + ' | '.join(options) + ')')
            else:
                options = []
            
            # set default input
            default = ''
            if '__default__' in option_spec:
                default = data[name].iloc[-1]

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
                while key != 'q' and key != '':
                    value_completer = tab_completer(past_df.get(key, []))
                    readline.set_completer(value_completer)
                    value = input('value: > ')
                    if value != 'q' and value != '':
                        response[key] = value
                    readline.set_completer(key_completer)
                    key = input('key: > ')
                response = json.dumps(response)
            # single input
            else:
                # set tab completion function
                completer = tab_completer(options)
                readline.set_completer(completer)
                # autofill with previous answer or default if any
                fill = str(row.get(name, '')) or default
                if fill:
                    readline.set_startup_hook(lambda: readline.insert_text(fill))
                # read response
                response = input("> ")
                # reset autofill
                readline.set_startup_hook()
            row[name] = response
            i += 1
        except KeyboardInterrupt:
            options = ['quit', 'q', 'write and quit', 'wq', 'back']
            completer = tab_completer(options)
            readline.set_completer(completer)
            readline.set_startup_hook()
            print('\n\nKeyboardInterrupt')
            print('  (' + ' | '.join(map(str, options)) + ')')
            response = input("> ")
            if response == 'quit' or response == 'q':
                raise
            elif response == 'write and quit' or response == 'wq':
                break
            elif response == 'back':
                i -= 1



if replace_data:
    data.drop(idx, axis=0, inplace=True)
data = data.append(row, ignore_index=True)
data.to_csv(data_path, index=False)
