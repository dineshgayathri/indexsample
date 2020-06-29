import pymongo
import csv
import codecs
import base64
import torf
import guessit
from configparser import ConfigParser

parser = ConfigParser()
parser.read('config.ini')

#https://web.archive.org/web/20190924160713/https://thepiratebay.org/static/dump/csv/torrent_dump_full.csv.gz


def buildmagnet(b64, name, sz, tr):
    base64_message = b64
    base64_bytes = base64.b64decode(base64_message)
    hash = ''.join(format(x, '02X') for x in base64_bytes)
    magnet = torf.Magnet(
        xt='urn:btih:' + hash,
        dn=name,
        tr=tr,
        xl=sz)

    return str(magnet), hash

trackers = None
with open("trackers.txt") as trk_file:
    trackers = trk_file.readlines()

dump_file = parser.get('offlinebay', 'dump_file')

client = pymongo.MongoClient()
cdb = client['magnets']

max_records = parser.getint('offlinebay', 'max_records')
mondb = cdb.magnets
with codecs.open(dump_file, 'r', encoding='utf-8') as csv_file:
    count = 0
    err_count = 0
    for line in csv_file:
        try:
            csv_reader = csv.reader([line], delimiter=';')
            for row in csv_reader:
                if len(row[1]) != 28:
                    continue
                info = guessit.guessit(row[2])
                if 'title' not in info:
                    continue
                try:
                    magnet, hash = buildmagnet(row[1], row[2], row[3], trackers)
                except torf.MagnetError:
                    continue
                map = {
                    '_id': hash,
                    'title': info['title'],
                    'name': row[2],
                    'magnet': magnet,
                }

                count += 1
                try:
                    mondb.insert_one(map)
                except pymongo.errors.DuplicateKeyError:
                    err_count += 1

        except IndexError:
            pass
        except csv.Error:
            pass

        if count > max_records: #XXX remove
            break

    print('dup errors', err_count, 'count', count)
