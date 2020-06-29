import requests
import os
import json
import codecs
import time
import pymongo
from configparser import ConfigParser

parser = ConfigParser()
parser.read('config.ini')

def scrape_mblock(movie_block):
    movieb_data = {}

    if 'torrents' not in movie_block:
        return False

    size = 0
    for torrent in movie_block['torrents']:
        if size < torrent['size_bytes']:
            size = torrent['size_bytes']

            movieb_data['_id'] = torrent['hash']
            movieb_data['torrent'] = torrent['url']

            try:
                movieb_data['seeds'] = movie_block['seeds']
            except:
                movieb_data['seeds'] = None

            try:
                movieb_data['leeches'] = movie_block['peers']
            except:
                movieb_data['leeches'] = None

    movieb_data['dbid'] = movie_block['imdb_code']
    movieb_data['year'] = movie_block['year']
    movieb_data['title'] = movie_block['title']

    return movieb_data


def scrape_this(root_url, ll, sitemap_file):

    pages = []
    if os.path.exists(sitemap_file):
        with codecs.open(sitemap_file, 'r', encoding='utf-8') as f:
            pages = json.load(f)
    else:
        to_scrap = []

        for l in ll:
            url = root_url % (l,)
            to_scrap.append(url)

        print("Going over XMLs...")
        for url in help_routines.sample(to_scrap, parser.getint('yts', 'to_scrap')): #XXX to_scrap
            print(url)
            source = requests.get(url).text
            try:
                j = json.loads(source)
                for movie in j['data']['movies']:
                    pages.append(movie)
            except json.decoder.JSONDecodeError:
                print('parse failed')
                pass
            time.sleep(0.1)

        with codecs.open(sitemap_file, 'w', encoding='utf-8') as f:
            json.dump(pages, f, ensure_ascii=False, indent=4)

    client = pymongo.MongoClient()
    cdb = client['magnets']

    mondb=cdb.magnets
    print("going over pages", len(pages))
    err_count = 0
    for j in pages:

        map = scrape_mblock(j)
        if not map:
            continue

        try:
            mondb.insert_one(map)
        except pymongo.errors.DuplicateKeyError:
            err_count += 1

    print('dup errors', err_count)


scrape_this("https://yts.mx/api/v2/list_movies.json?limit=50&page=%d", range(1, 363), 'yts.pages.json')

