from pymongo import MongoClient

client = MongoClient()

cdb1 = client['imdb']
imdb=cdb1.imdb

cdb2 = client['magnets']
magnets=cdb2.magnets

count = 0
updates = {}
for document in magnets.find():
    if 'dbid' in document:
        dbid = document['dbid']
        if dbid == 'tt' and document['title'] == '':
            updates[document['_id']] = {'invalid': True}
            continue

        im = imdb.find_one({'_id': dbid})
        print(dbid, im)
        if im:
            if 'title' in document:
                if im['title'] != document['title']:
                    print(im, document)
            count += 1
            if count > 10:
                break

print(updates)