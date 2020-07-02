import bs4
import requests
import re
import time
import pymongo
import guessit
from configparser import ConfigParser
import help_routines

parser = ConfigParser()
parser.read('config.ini')

category_list = set()
category_list.add('TV')
category_list.add('Movies')


def scrape_mblock(movie_block):
    movieb_data = {}

    divs = movie_block.findAll('div', {'class', 'dltorrent'})
    magnets = set()
    for div in divs:
        As = div.findAll('a')
        for a in As:
            href = a.get('href')
            if href.startswith('magnet:'):
                magnets.add(href)

    try:
        name = movie_block.find('div', {'id': 'content'}).find('h1').text
        movieb_data['name'] = name
        info = guessit.guessit(name)
        movieb_data['title'] = info['title']
    except:
        return False, None

    try:
        movieb_data['seeds'] = str(
            movie_block.find('span', {'class': 'greenish'}).text)
    except:
        movieb_data['seeds'] = None

    try:
        movieb_data['leeches'] = str(
            movie_block.find('span', {'class': 'reddish'}).text)
    except:
        movieb_data['leeches'] = None

    return movieb_data, list(magnets)


def scrape_this(root_url, ll, sitemap_file):

    pages = []
    to_scrap = []

    for l in ll:
        url = root_url % (l,)
        to_scrap.append(url)

    print("Going over XMLs...")
    for url in help_routines.sample(to_scrap, parser.getint('limetorrents', 'to_scrap')): #XXX to_scrap
        print(url)
        source = requests.get(url).text
        soup = bs4.BeautifulSoup(source, 'xml')
        sitemap = soup.findAll('loc')
        for loc in sitemap:
            pages.append(loc.text)

    print("going over pages", len(pages))

    hash_re = re.compile('btih:([0-9|A-Z|a-z]*)&.*')

    client = pymongo.MongoClient()
    cdb = client['magnets']

    mondb = cdb.magnets
    err_count = 0
    for url in help_routines.sample(pages, parser.getint('limetorrents', 'pages')): #XXX pages

        print(url)
        source = requests.get(url).text
        soup = bs4.BeautifulSoup(source, 'html.parser')

        map, magnets = scrape_mblock(soup)
        if not map:
            continue

        for magnet in magnets:
            m = hash_re.search(magnet)
            hash = m.group(1).upper()
            map['_id'] = hash
            map['magnet'] = magnet
            try:
                mondb.insert_one(map)
            except pymongo.errors.DuplicateKeyError:
                err_count += 1

        time.sleep(0.1)

scrape_this("https://limetorrents.info/sitemaps/allsitemap%d.xml", range(1, 328), 'limetorrents.pages.txt')

