import pymongo
import guessit
import os
import rank

include_video_ext = set()
include_video_ext.add('.mkv')
include_video_ext.add('.mp4')
include_video_ext.add('.m4v')
include_video_ext.add('.mpg')
include_video_ext.add('.avi')
include_video_ext.add('.mpeg')

client = pymongo.MongoClient()
cdb1 = client['magnets']
magnets = cdb1.magnets
nzbs = cdb1.nzbs

cdb2 = client['downloads']
downloads = cdb2.downloads
downloads.drop()

cdb3 = client['imdb']
imdb = cdb3.imdb

for document in magnets.find({'files': {'$exists': True}}):
    for file in document['files']:
        path = file['path']
        size = file['size']
        if isinstance(path, list):
            path = path[0]
        extension = os.path.splitext(path)[1].lower()
        if extension in include_video_ext:
            name = os.path.basename(path)
            info = guessit.guessit(name)
            for key, value in list(info.items()):
                if not isinstance(value, (int, str, float)):
                    info[key] = str(value)

            if 'season' not in info or 'episode' not in info:
                value = {'hash': document['_id'], 'name': name, 'size': size, 'extra': info}
                downloads.update_one(
                    {'_id': document['title']},
                    {
                        '$set': {'title': document['title'], 'dbid': document['dbid']},
                        '$push': {'files': value}
                    }, upsert=True
                )
            else:
                episode = 'S%02dE%02d' % (info['season'], info['episode'],)
                key = '%s\t%s' % (document['title'], episode,)
                value = {'hash': document['_id'], 'name': name, 'size': size, 'extra': info}
                downloads.update_one(
                    {'_id': key},
                    {
                        '$set': {'title': document['title'], 'dbid': document['dbid'], 'episode': episode},
                        '$push': {'files': value}
                    }, upsert=True
                )

for document in nzbs.find():
    name = document['name']
    info = guessit.guessit(name)
    for key, value in list(info.items()):
        if isinstance(value, (int, str, float)):
            pass
        elif isinstance(value, list):
            x = []
            for v in value:
                if isinstance(v, (int, str, float)):
                    x.append(v)
                else:
                    x.append(str(v))
            info[key] = x
        else:
            info[key] = str(value)

    if document['type'] == 'Movie':
        value = {'guid': document['_id'], 'name': name, 'extra': info}
        downloads.update_one(
            {'_id': info['title']},
            {
                '$set': {'title': info['title']},
                '$push': {'files': value}
            }, upsert=True
        )
    else:
        if 'season' not in info:
            continue
        if isinstance(info['season'], list):
            continue
        
        if 'episode' not in info:
            im = imdb.find_one({'_id': document['dbid']})
            episodes = range(1, 1+im['seasons']['S%02d' % (info['season'],)])
        elif isinstance(info['episode'], list):
            episodes = info['episode']
        else:
            episodes = [info['episode']]
        for e in episodes:
            episode = 'S%02dE%02d' % (info['season'], e,)
            key = '%s\t%s' % (info['title'], e,)
            value = {'guid': document['_id'], 'name': name, 'extra': info}
            downloads.update_one(
                {'_id': key},
                {
                    '$set': {'title': info['title'], 'dbid': document['dbid'], 'episode': episode},
                    '$push': {'files': value}
                }, upsert=True
            )

for document in downloads.find():
    files = sorted(document['files'], key=rank.score)
    downloads.update_one({'_id': document['_id']}, {'$set': {'files': files}})