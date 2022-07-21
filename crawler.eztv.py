import requests
import json
import time
import pymongo
import re
import help_routines
from configparser import ConfigParser

parser = ConfigParser()
parser.read('config.ini')

def scrape_mblock(movie_block) -> dict:
    movieb_data = {}

    movieb_data['magnet'] = movie_block['magnet_url']

    if str(movie_block['imdb_id']) not in ['', '0']:
        movieb_data['dbid'] = 'tt%s' % (movie_block['imdb_id'])
    movieb_data['name'] = movie_block['filename']
    movieb_data['seeds'] = movie_block['seeds']
    movieb_data['leeches'] = movie_block['peers']

    return movieb_data


def scrape_this(root_url : str, ll, sitemap_file : str):

    pages = []
    to_scrap = []

    for l in ll:
        url = root_url % (l,)
        to_scrap.append(url)

    print("Going over XMLs...")
    for url in help_routines.sample(to_scrap, parser.getint('eztv', 'to_scrap')):
        print(url)
        source = requests.get(url).text
        try:
            j = json.loads(source)
            for torrent in j['torrents']:
                pages.append(torrent)
        except json.decoder.JSONDecodeError:
            print('parse failed')
            pass
        time.sleep(0.1)

    client = pymongo.MongoClient()
    cdb = client['magnets']

    mondb=cdb.magnets
    print("going over pages", len(pages))
    hash_re = re.compile('btih:([0-9|A-Z|a-z]*)&.*')
    err_count = 0
    for j in pages:

        map = scrape_mblock(j)

        m = hash_re.search(map['magnet'])
        hash = m.group(1).upper()
        map['_id'] = hash
        try:
            mondb.insert_one(map)
        except pymongo.errors.DuplicateKeyError:
            err_count += 1

    print('dup errors', err_count)


# XXX why go over list like this - and then pass it to the function?!
scrape_this("https://eztv.ro/api/get-torrents?limit=100&page=%d", range(1, 2863), 'eztv.pages.json')

