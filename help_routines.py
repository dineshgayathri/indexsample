import re
import random

def fix_name(name):
    new_name = re.sub(r'[!:\'\?]', '', name)
    return new_name.lower().replace('-',' ')

def sample(items, s):
    return random.sample(items, min(len(items), s))