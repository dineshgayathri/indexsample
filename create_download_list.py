import pymongo
import guessit
import os
import rank
import help_routines
import sys

include_video_ext = set()
include_video_ext.add('.mkv')
include_video_ext.add('.mp4')
include_video_ext.add('.m4v')
include_video_ext.add('.mpg')
include_video_ext.add('.avi')
include_video_ext.add('.mpeg')

include_subs_ext = set()
include_subs_ext.add('.sub')
include_subs_ext.add('.srt')

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
    to_add = {}
    for file in document['files']:
        path = file['path']
        size = file['size']
        if isinstance(path, list):
            path = path[-1]
        
        s = os.path.splitext(os.path.basename(path))
        extension = s[1].lower()
        key = s[0].lower()
        if extension in include_video_ext:
            basename = os.path.basename(path)
            info = help_routines.fix_dict(guessit.guessit(basename))
            info.update({
                'partial_sub': 0,
                'exact_sub': 0
            })
            to_add[key] = {
                'name': basename,
                'info': info,
                'size': size,
                'path': path
            }

    for file in document['files']:
        path = file['path']
        size = file['size']
        if isinstance(path, list):
            path = path[-1]

        s = os.path.splitext(os.path.basename(path))
        extension = s[1].lower()
        key = s[0].lower()
        if extension in include_subs_ext:
            if key in to_add:
                to_add[key]['info']['exact_sub'] += 1
                
            elif len(to_add) == 1:
                to_add[next(iter(to_add))]['info']['partial_sub'] += 1

            else:
                pass
                #print('subtitle ignored')

    for name, data in to_add.items(): 
            if 'season' not in data['info'] or 'episode' not in data['info']:
                value = {'hash': document['_id'], 'name': data['name'], 'size': data['size'], 'extra': data['info']}
                downloads.update_one(
                    {'_id': document['title']},
                    {
                        '$set': {'title': document['title'], 'dbid': document['dbid']},
                        '$push': {'files': value}
                    }, upsert=True
                )
            else:
                episodes = help_routines.build_episodes(imdb, document['dbid'], data['info'])
                for episode in episodes:
                    key = '%s\t%s' % (document['title'], episode,)
                    value = {'hash': document['_id'], 'name': data['name'], 'size': data['size'], 'extra': data['info']}
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
    info = help_routines.fix_dict(guessit.guessit(name))

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
        episodes = help_routines.build_episodes(imdb, document['dbid'], info)
        for episode in episodes:
            key = '%s\t%s' % (info['title'], episode,)
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
