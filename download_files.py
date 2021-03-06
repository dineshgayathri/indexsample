import pymongo
import os
from configparser import ConfigParser
import time
from datetime import datetime, timedelta
import random
import sys
import help_routines
from pythonopensubtitles.opensubtitles import OpenSubtitles
from pythonopensubtitles.utils import File
import tempfile
import shutil

#need to run more than once, because of multiple files torrents that can fail
#the easiest way is to download subtitles by file hash and language both in open_subtitles and in addic7ed

parser = ConfigParser()
parser.read('config.ini')

client = pymongo.MongoClient()
cdb1 = client['magnets']
magnets = cdb1.magnets
nzbs = cdb1.nzbs

cdb2 = client['downloads']
downloads = cdb2.downloads

cdb3 = client['imdb']
imdb = cdb3.imdb

ost = OpenSubtitles() 
ost.login(parser.get('sub','user'), parser.get('sub','pass'))

def download_subtitles(folder, file):
    video_path = os.path.join(folder, file)
    f = File(video_path)

    data = ost.search_subtitles([{'sublanguageid': 'all', 'moviehash': f.get_hash(), 'moviebytesize': f.size}])
    if data:
        id_subtitle_file = data[0].get('IDSubtitleFile')

        tempdir = tempfile.mkdtemp()
        d = ost.download_subtitles([id_subtitle_file], output_directory=tempdir, extension='srt')
        for k, v in d.items():
            pre, ext = os.path.splitext(video_path)
            os.rename(v, pre + '.srt')
        shutil.rmtree(tempdir, ignore_errors=True)

    sys.exit(9)

class STATUS():
    Queued = 'Queued'
    Completed = 'Completed'
    Failed = 'Failed'
    Exhausted = 'Exhausted'


class DOWNLOADER_TYPE():
    Torrent = 'Torrent'
    NZB = 'nzb'


def touch(path: str):
    with open(path, 'a'):
        os.utime(path, None)


class Downloader():
    def __init__(self, queue_size: int):
        self.queue_size = queue_size
        self.active_queue = {}
        self.ended_queue = {}
        self.last_id = 0
        self.downloaded = set()
        pass

    def queue_full(self):
        return len(self.active_queue) > self.queue_size

    def add_download(self, file, dbid, episode, files):
        self.last_id += 1
        id = self.last_id
        if 'hash' in file:
            type = DOWNLOADER_TYPE.Torrent
            key = file['hash']
            doc = magnets.find_one({'_id': key})
            if 'magnet' in doc:
                #XXX add download to queue
                print("adding download to", dbid, episode, doc['magnet'])
            else:
                #XXX add download to queue
                print("adding download to", dbid, episode, doc['torrent'])
        else:
            type = DOWNLOADER_TYPE.NZB
            key = file['guid']
            doc = nzbs.find_one({'_id': key})
            #XXX add download to queue
            print(dbid, episode, f"nzbs/{doc['name']}.nzb")

        if key in self.downloaded:
            return None
        else:
            self.downloaded.add(key)

        state = {
            'type': type,
            'download_id': id,
            'file': file,
            'files': files,
            'dbid': dbid,
            'episode': episode,
            'status': STATUS.Queued,
            'expired': datetime.now()+timedelta(seconds=random.randint(0, 10))}

        self.active_queue[id] = state
        return state

    def move_download(self, state):
        #XXX download ended move files to proper location
        print('move_download', state)
        path = parser.get('downloader', 'output_path') + '/' + state['dbid']
        if state.get('episode'):
            episodes = help_routines.build_episodes(imdb, state['dbid'], state['file']['extra'])
            for episode in episodes:
                path1 = path + '/' + episode
                if not os.path.exists(path1):
                    os.mkdir(path1)
                touch(f"{path1}/video.mkv")
                if state['file']['extra']['exact_sub'] > 0:
                    touch(f"{path1}/video.srt")
                else:
                    download_subtitles(path1, "video.mkv")
        else:
            touch(f"{path}/video.mkv")
            if state['file']['extra']['exact_sub'] > 0:
                touch(f"{path}/video.srt")
            else:
                download_subtitles(path, "video.mkv")

    def check_state(self, id):
        #XXX check status of download
        state = self.active_queue[id]
        if state['expired'] < datetime.now():
            if random.randint(1, 10) > 8:
                status = STATUS.Failed
                print('failed')
            else:
                status = STATUS.Completed
                print('completed')
            state['status'] = status
            self.ended_queue[id] = state
            del self.active_queue[id]

        return state['status']

    def get_queue(self):
        return list(self.active_queue.items())

    def update_status(self, id, status):
        assert(id not in self.active_queue)
        self.ended_queue[id]['status'] = STATUS.Exhausted

downloader = Downloader(parser.getint('downloader', 'queue_size'))

for document in downloads.find():
    if 'dbid' not in document:
        print('not dbid, ignoring')
        continue
    path = parser.get('downloader', 'output_path') + '/' + document['dbid']
    if not os.path.exists(path):
        os.makedirs(path)
    if 'episode' in document:
        path = path + '/' + document['episode']
        if not os.path.exists(path):
            os.mkdir(path)
    if os.listdir(path):
        continue

    while downloader.queue_full():
        for id, state in downloader.get_queue():
            if state['status'] == STATUS.Queued:
                download_status = downloader.check_state(state['download_id'])
                if download_status == STATUS.Queued:
                    continue

                if download_status == STATUS.Completed:
                    downloader.move_download(state)
                else:
                    prev_found = False
                    added_new = False
                    for file in state['files']:
                        if prev_found:
                            state = downloader.add_download(file, state['dbid'], state.get('episode'), state['files'])
                            if not state:
                                continue

                            added_new = True
                            break
                        if 'hash' in file and 'hash' in state:
                            if state['hash'] == file['hash']:
                                prev_found = True
                                continue
                        elif 'guid' in file and 'guid' in state:
                            if state['guid'] == file['guid']:
                                prev_found = True
                                continue
                    if not added_new:
                        downloader.update_status(state['download_id'], STATUS.Exhausted)

        time.sleep(1)

    for file in document['files']:
        state = downloader.add_download(file, document['dbid'], document.get('episode'), document['files'])
        if not state:
            continue

