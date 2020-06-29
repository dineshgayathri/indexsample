import re

def fix_name(name):
    newname = re.sub('[!:\'\?]', '', name)
    return newname.lower().replace('-',' ')