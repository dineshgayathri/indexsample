import concurrent.futures
from sys import platform
if platform == "linux" or platform == "linux2":
    import libtorrent as lt
from time import sleep
import tempfile
import shutil
import pymongo
from bcoding import bencode, bdecode
import requests

def magnet2torrent(hash, magnet):

    s = {}
    if platform == "linux" or platform == "linux2":
        tempdir = tempfile.mkdtemp()
        ses = lt.session()
        params = {
            'save_path': tempdir,
            'storage_mode': lt.storage_mode_t(2),
        }
        handle = lt.add_magnet_uri(ses, magnet, params)

        tries = 0
        while (not handle.has_metadata()):
            if tries > 10:
                break
            sleep(1)
            tries += 1
        ses.pause()

        if handle.has_metadata():
            info = handle.get_torrent_info()
            s[hash] = {'files': []}
            for f in info.files():
                s[hash]['files'].append({'path': f.path, 'size': f.size})

            ses.remove_torrent(handle)
        shutil.rmtree(tempdir, ignore_errors=True)
    return s

def parse_torrent(torrent):
    data = requests.get(torrent).content
    try:
        torrent = bdecode(data)

        files = []
        for file in torrent["info"]["files"]:
            files.append({'path': file["path"], 'size': file["length"]})
        return files
    except TypeError:
        print('error', torrent)
        return False

def main():
    client = pymongo.MongoClient()
    cdb = client['magnets']

    mondb = cdb.magnets
    mlist = {}
    rlist = {}
    for document in mondb.find():
        if 'dbid' not in document:
            continue
        hash = document['_id']
        if 'magnet' in document:
            magnet = document['magnet']
            mlist[hash] = magnet
        else:
            torrent = document['torrent']
            rlist[hash] = torrent

    print(len(mlist), len(rlist))

    i = 0
    data = [(k, v) for k, v in mlist.items()]
    chunks = [data[x:x + 1000] for x in range(0, len(data), 1000)]
    for chunk in chunks:
        with concurrent.futures.ProcessPoolExecutor(max_workers=50) as executor:
            futures = {executor.submit(magnet2torrent, hash, magnet) for hash, magnet in chunk}
            for future in concurrent.futures.as_completed(futures):
                data = future.result()
                for hash, files in data.items():
                    mondb.update_one({'_id': hash}, {'$set': files})
        print(i)
        i += 1

    for hash, torrent in rlist.items():
        files = parse_torrent(torrent)
        if files:
            mondb.update_one({'_id': hash}, {'$set': {'files': files}})

if __name__ == '__main__':
    main()