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

bag <survey_name> [-e | --editor[=<int>]]
- begins prompting for answers to questions defined in {script_path}/surveys/<survey_name>.yaml
- saves responses as a row in {script_path}/data/<survey_name>.yaml
- editor flag opens the row in a text editor (set by environment var $EDITOR) rather than going through survey incrementally. Only written for Unix at the moment. Intended mainly for daily surveys.
  - <int> argument to editor flag gives offset w/r/t today in units of days for row lookup for daily surveys
"""

arg_iter = iter(sys.argv[1:])
spec = None
editor = False
offset = 0
for arg in arg_iter:
    if arg == '-h' or arg == '--help':
        print(help_text)
        sys.exit(0)
    elif '--editor' in arg or arg == '-e':
        editor = True
        try:
            # accept 'offset' argument to flat
            offset = int(arg.split('=')[1])
        except Exception:
            pass
    elif '-o' in arg:
        try:
            # accept 'offset' argument to flat
            offset = int(arg.split('=')[1])
        except Exception:
            pass
    elif spec is None and os.path.exists(f'{script_path}/surveys/{arg}.yaml'):
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
today = data.loc[data['date']==(datetime.date.today() + datetime.timedelta(offset)).isoformat()]
if 'daily' in spec.keys() and not today.empty:
    replace_data = True
    [idx] = today.index.values
    today = today.iloc[0]
    row = today.to_dict()
else:
    # initialize data row with keys only
    row = {q[0]: '' for q in questions}

# autogen date/time cols
row['date'] = (datetime.date.today() + datetime.timedelta(offset)).isoformat()
row['time'] = datetime.datetime.now().time().isoformat(timespec='minutes')


# Quick data input in text editor
if editor:
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
            # list past answers as options
            if '__past__' in option_spec:
                options = data[name].iloc[::-1].unique()
                print('  (' + ' | '.join(map(str, options)) + ')')
            # or past words
            elif '__past_words__' in option_spec:
                options = data[name].iloc[::-1]
                options = ' '.join(options).split()
                options = pd.unique(options)
                print('  (' + ' | '.join(map(str, options)) + ')')
            # or specified options
            elif len(option_spec) > 0:
                options = option_spec
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
                # autofill with previous answer if any
                fill = str(row.get(name, ''))
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
