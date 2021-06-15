#!/usr/bin/python3

import yaml
import sys
import os
import pandas as pd

arg_iter = iter(sys.argv[1:])
spec = None
for arg in arg_iter:
    if spec is None and os.path.exists(f'surveys/{arg}.yaml'):
        data_path = f'data/{arg}.csv'
        try:
            data = pd.read_csv(data_path)
        except FileNotFoundError:
            data = None
        spec = yaml.load(f'surveys/{arg}.yaml')
    else:
        raise Exception(f'Argument {arg} not supported or survey not found')

print(spec)

# initialize data frame if absent
