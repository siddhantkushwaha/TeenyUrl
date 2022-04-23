import json
import os

root_dir = os.path.dirname(os.path.realpath(__file__))

with open(os.path.join(root_dir, 'config', 'config.json'), 'r') as fp:
    config = json.load(fp)

with open(os.path.join(root_dir, 'config', 'tokens.json'), 'r') as fp:
    tokens = json.load(fp)

hostname = config['hostname']
