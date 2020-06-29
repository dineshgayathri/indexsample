import pymongo
import guessit
import os

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
                value = {'hash': document['_id'], 'name': name, 'size': size}
                downloads.update_one(
                    {'_id': document['title']},
                    {
                        '$set': {'title': document['title']},
                        '$push': {'files': value, 'extra': info}
                    }, upsert=True
                )
            else:
                episode = 'S%02dE%02d' % (info['season'], info['episode'],)
                key = '%s\t%s' % (document['title'], episode,)
                value = {'hash': document['_id'], 'name': name, 'size': size}
                downloads.update_one(
                    {'_id': key},
                    {
                        '$set': {'title': document['title'], 'episode': episode},
                        '$push': {'files': value, 'extra': info}
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

    if 'season' not in info or 'episode' not in info:
        value = {'guid': document['_id'], 'name': name}
        downloads.update_one(
            {'_id': info['title']},
            {
                '$set': {'title': info['title']},
                '$push': {'files': value, 'extra': info}
            }, upsert=True
        )
    else:
        if isinstance(info['episode'], list):
            episodes = info['episode']
        else:
            episodes = [info['episode']]
        for e in episodes:
            episode = 'S%02dE%02d' % (info['season'], e,)
            key = '%s\t%s' % (info['title'], e,)
            value = {'guid': document['_id'], 'name': name}
            downloads.update_one(
                {'_id': key},
                {
                    '$set': {'title': info['title'], 'episode': episode},
                    '$push': {'files': value, 'extra': info}
                }, upsert=True
            )
