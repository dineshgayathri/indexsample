import rarbgapi
from rarbgapi.rarbgapi import request
import pymongo
import re
from configparser import ConfigParser

parser = ConfigParser()
parser.read('config.ini')

class RarbgAPI(rarbgapi.RarbgAPI):
    # Exposes IMDB search

    def __init__(self, **options):
        super(RarbgAPI, self).__init__()

    @request
    def search_imdb(self, imdb_id , **kwargs):
        if isinstance(imdb_id, int):
            imdb_id = f"tt{imdb_id:06}"
        elif not imdb_id.startswith("tt"):
            imdb_id = f"tt{imdb_id}"

        return self._query('search', search_imdb=imdb_id, **kwargs)

hash_re = re.compile('btih:([0-9|A-Z|a-z]*)&.*')

rarbgclient = RarbgAPI()

client = pymongo.MongoClient()

cdb = client['magnets']
magnets=cdb.magnets

dbids = {}
for document in magnets.find({'dbid': {'$exists': True}}):
    dbids[document['dbid']] = document['title']

added = 0
err_count = 0
for dbid, title in help_routines.sample(dbids.items(), parser.getint('rarbg', 'ids')):

    try:
        c = rarbgclient.search_imdb(dbid, limit=100, format_="json_extended")
    except:
        continue
    for torrent in c:
        map = {}
        j = torrent._raw

        magnet = j['download']

        m = hash_re.search(magnet)
        hash = m.group(1).upper()
        map['_id'] = hash
        map['magnet'] = magnet
        map['category'] = j['category']
        map['name'] = j['title']
        map['seeders'] = j['seeders']
        map['leechers'] = j['leechers']
        map['dbid'] = dbid
        map['title'] = title

        try:
            magnets.insert_one(map)
            added += 1
        except pymongo.errors.DuplicateKeyError:
            err_count += 1

print(f'added {added} duplicates {err_count}')

