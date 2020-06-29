from tmdbv3api import TMDb, Movie, TV, Episode, Season
import pymongo
from configparser import ConfigParser

parser = ConfigParser()
parser.read('config.ini')



def main():
    tmdb = TMDb()
    tmdb.api_key = parser.get('tmdb', 'key')

    m = Movie()

    client = pymongo.MongoClient()
    cdb = client['magnets']

    mondb = cdb.magnets
    dbids = set()
    for document in mondb.find({'files': {'$exists': True}}):
        dbids.add(document['dbid'])

    cdb = client['imdb']

    mondb = cdb.imdb

    for dbid in dbids:
        document = mondb.find_one({'_id': dbid})

        r = m.external(dbid, "imdb_id")
        updates = {}
        if len(r['tv_results']) == 1:
            if document['type'] != 'TVSeries':
                mondb.update_one({'_id': dbid}, {'$set': {'type': 'TVSeries'}})
            sid = r['tv_results'][0]['id']
            tv = TV()
            series = tv.details(sid)
            seasons = {}
            for season in series.seasons:
                seasons['S%02d' % season['season_number']] = season['episode_count']
            updates['seasons'] = seasons
        else:
            assert(document['type'] == 'Movie')
            continue

        mondb.update_one({'_id': dbid}, {'$set': updates})

if __name__ == '__main__':
    main()
