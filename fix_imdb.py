import pymongo
import help_routines
import requests
import bs4
import json

nf = set()
def get_imdb_title(imdb, monsectvdb, monsecmoviedb, dbid):

    if dbid in nf:
        return None

    url = 'https://www.imdb.com/title/%s/' % (dbid,)
    print(url)
    source = requests.get(url).text
    
    soup = bs4.BeautifulSoup(source, 'html.parser')

    try:
        scripttext = soup.find('script', type='application/ld+json').contents
    except:
        nf.add(dbid)
        return None

    script = json.loads(scripttext[0])
    title = script['name']
    data = {'_id': dbid, 'title': title, 'href': script['url'], 'type': script['@type']}
    imdb.insert_one(data)

    try:
        sec = {
            '_id': help_routines.fix_name(script['name']),
            'dbid': dbid,
        }
        if type == 'TVSeries':
            monsectvdb.insert_one(sec)
        else:
            monsecmoviedb.insert_one(sec)

    except pymongo.errors.DuplicateKeyError as e:
        print('key already exists', dbid)

    return title


client = pymongo.MongoClient()

cdb1 = client['imdb']
imdb=cdb1.imdb
monsectvdb = cdb1.sectvdb
monsecmoviedb = cdb1.secmoviedb

cdb2 = client['magnets']
magnets=cdb2.magnets

updates = {}
for document in magnets.find():
    if 'dbid' in document:
        dbid = document['dbid']

        im = imdb.find_one({'_id': dbid})
        if im:
            if im['title'] != document.get('title'):
                updates[document['_id']] = {'$set': {'title': im['title']}}
        else:
            title = get_imdb_title(imdb, monsectvdb, monsecmoviedb, dbid)
            if title:
                updates[document['_id']] = {'$set': {'title': title}}
            else:
                updates[document['_id']] = {'$unset': {'dbid': ''}}
    else:
        if 'title' in document:
            im = imdb.find_one({'_id': help_routines.fix_name(document['title'])})
            if im:
                t = imdb.find_one({'_id': im['dbid']})
                updates[document['_id']] = {'$set': {'dbid': im['dbid'], 'title': t['title']}}

for key, data in updates.items():
    if data:
        magnets.update_one({'_id': key}, data)

print('updates', len(updates))

