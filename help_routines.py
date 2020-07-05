import re
import random
import json

def fix_name(name):
    new_name = re.sub(r'[!:\'\?]', '', name)
    return new_name.lower().replace('-',' ')

def sample(items, s):
    return random.sample(items, min(len(items), s))

def build_episodes(imdb, dbid, info):
    if 'season' not in info:
        return []
    if isinstance(info['season'], list):
        return []

    if 'episode' not in info:
        im = imdb.find_one({'_id': dbid})
        episodes = range(1, 1 + im['seasons']['S%02d' % (info['season'],)])
    elif isinstance(info['episode'], list):
        episodes = info['episode']
    else:
        episodes = [info['episode']]
    ret = []
    for e in episodes:
        episode = 'S%02dE%02d' % (info['season'], e,)
        ret.append(episode)

    return ret

def fix_dict(info):
    newdict = {}
    for key, value in list(info.items()):
        if isinstance(value, (int, str, float)):
            newdict[key] = value
        elif isinstance(value, list):
            x = []
            for v in value:
                if isinstance(v, (int, str, float)):
                    x.append(v)
                else:
                    x.append(str(v))
            newdict[key] = x
        else:
            newdict[key] = str(value)

    return newdict