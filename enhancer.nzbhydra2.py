import pymongo
import configparser
import requests
import os.path
import help_routines
from configparser import ConfigParser

parser = ConfigParser()
parser.read('config.ini')

# NZBHydra2 server is required.
# Please check https://github.com/theotherp/nzbhydra2/ for details.

NH_SERVER = parser.get('nzbhydra2', 'host')
API_KEY = parser.get('nzbhydra2', 'key')


# check https://github.com/mrobinsn/go-newznab/blob/cd89d9c56447859fa1298dc9a0053c92c45ac7ef/newznab/newznab.go

def search(query=None,db=None, id_=None, category=None, season=None, episode=None):
    params = {"apikey": API_KEY, "o":"json"}
    if category == "tv":
        params["t"] = "tvsearch"
    elif category == "movie":
        params["t"] = "movie"

    if db == "tvmaze":
        params["tvmazeid"] = id_
    elif db == "tvdb":
        params["tvdbid"] = id_
    elif db == "tvrage":
        params["rid"] = id_
    elif db == "tvdb":
        params["tvdbid"] = id_
    elif db == "imdb":
        params["imdbid"] = id_

    if episode is not None:
        params["episode"] = episode
    if season is not None:
        params["season"] = season

    if query is not None:
        params["q"] = query

    r = requests.get(f"http://{NH_SERVER}/api", params = params)

    if r.status_code != 200:
        print(f"got status code {r.status_code} for {r.url}")
        return []
    print(r.url)
    return r.json()

def search_tv_by_imdb(imdb_id, season=None,episode=None):
    return search(db="imdb", id_=imdb_id, category="tv", season=season, episode=episode)

def search_movie_by_imdb(imdb_id):
    return search(db="imdb", id_=imdb_id, category="movie")

def parse_response(res):
    l = []
    items = res["channel"]["item"]
    for item in items:
        ep = {
            "name":item["title"],
            "nzburl": item["link"],
            "category": item["category"],
            "description": item["description"],
            }
        attrs = item["attr"]
        for attr in attrs:
            a = attr["@attributes"]
            if a["name"] in ("episode", "tvrageid", "season", "dbid", "tvmazeid"):
                ep[a["name"]]=a["value"]
            elif a["name"] == "imdbid":
                ep['tvdbid'] = 'tt'+a["value"]
            elif a["name"] == "guid":
                ep['_id'] = a["value"]
        l.append(ep)
    return l

def fetch_nzb(nzb, outdir=None):
    # fetch the NZB file
    r = requests.get(nzb["nzburl"])
    
    # 'Content-Disposition': 'attachment; filename="something.nzb"'
    fname = r.headers['Content-Disposition'].split(";")[1].split("=")[1][1:-1] # we can do better...
    if outdir:
        fname = os.path.join(outdir, fname)
    with open(fname, "w") as f:
        f.write(r.text)

client = pymongo.MongoClient()

cdb1 = client['magnets']
magnets=cdb1.magnets
nzbs=cdb1.nzbs

cdb2 = client['imdb']
imdb=cdb2.imdb

dbids = set()
for document in magnets.find({'dbid': {'$exists': True}}):

    dbids.add(document['dbid'])

dbids_to_search = {}
for dbid in dbids:
    document = imdb.find_one({'_id': dbid})
    dbids_to_search[dbid] = document

added = 0
err_count = 0
for dbid, document in help_routines.sample(dbids_to_search.items(), parser.getint('nzb', 'ids')): #XXX dbids_to_search.items()

    try:
        if document['type'] == 'Movie':
            r = search_movie_by_imdb(dbid)
            c=parse_response(r)
        else:
            # XXX search_tv_by_imdb() supports search by season & episode - we can use that
            # XXX This could be useful NZBHydra maxes out at 500 results (and indexers can max
            # XXX out even earlier)
            r = search_tv_by_imdb(dbid)
            c=parse_response(r)
    except:
        continue
    for nzb in help_routines.sample(c,parser.getint('nzb','pages')):  #XXX c:
        print(f"Adding {nzb['name']} ({document['title']})")
        try:
            nzb['type'] = document['type']
            nzbs.insert_one(nzb)
            added += 1
        except pymongo.errors.DuplicateKeyError:
            err_count += 1

        # Download the nzb itself
        fetch_nzb(nzb, "nzbs")

print(f'added {added} duplicates {err_count}')


