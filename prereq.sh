#!/bin/bash
pip install pymongo rarbgapi rarbgapi beautifulsoup4 guessit lxml torf bcoding tmdbv3api python-opensubtitles
wget https://web.archive.org/web/20190924160713/https://thepiratebay.org/static/dump/csv/torrent_dump_full.csv.gz
gunzip torrent_dump_full.csv.gz
