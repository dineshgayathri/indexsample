import re
import random

def fix_name(name):
    new_name = re.sub(r'[!:\'\?]', '', name)
    return new_name.lower().replace('-',' ')

def sample(items, s):
    return random.sample(items, min(len(items), s))

def build_episodes(imdb, dbid, info):
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