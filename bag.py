#!/usr/bin/python3

import yaml
import sys
import os
import pandas as pd
import json

arg_iter = iter(sys.argv[1:])
spec = None
for arg in arg_iter:
    if spec is None and os.path.exists(f'surveys/{arg}.yaml'):
        data_path = f'data/{arg}.csv'
        try:
            data = pd.read_csv(data_path)
        except FileNotFoundError:
            data = None
        with open(f'surveys/{arg}.yaml', 'r') as f:
            spec = yaml.load(f, Loader=yaml.SafeLoader)
    else:
        raise Exception(f'Argument {arg} not supported or survey not found')

#print(spec)

# initialize data frame if absent
if data is None:
    empty_data = {k:[] for k in spec['questions'].keys()}
    data = pd.DataFrame(empty_data)
# check if there are new questions
for q in spec['questions'].keys():
    if q not in data:
        data[q] = [None for _ in range(data.shape[0])]

# iterate through questions
questions = spec['questions'].items()

row = {}

for name,question in questions:
    print(question['query'])

    # list past answers as options
    if '__past__' in question.get('options', ''):
        print('  (' + ' | '.join(data[name].unique()) + ')')
    # ignore empty options
    elif not question.get('options', ''):
        pass
    else:
        print('  (' + ' | '.join(question.get('options', '')) + ')')
        
    # structured input
    if 'key-value' in question:
        response = {}
        key = input('key: > ')
        while key != 'q':
            value = input('value: > ')
            if value != 'q':
                response[key] = value
            key = input('key: > ')
        response = json.dumps(response)
    # single input
    else:
        response = input("> ")
    row[name] = response

# autogen date/time cols

data = data.append(row, ignore_index=True)
data.to_csv(data_path, index=False)
