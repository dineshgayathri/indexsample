import pymongo
import bs4
import requests
import guessit
import os
import codecs
import urllib.parse
import re
import random
from configparser import ConfigParser

parser = ConfigParser()
parser.read('config.ini')

category_list = set()
category_list.add('TV')
category_list.add('Movies')

prefix = 'https://www.imdb.com'
prog = re.compile("^/title/tt[0-9]+(/)?$")


def scrape_mblock(movie_block : bs4.BeautifulSoup) -> (dict, list):
    movieb_data = {}

    found = False
    try:
        spans = movie_block.find('div', {'class', 'col-9 page-content'}).findAll('span')
        for span in spans:
            if span.text in category_list:
                movieb_data['category']=span.text
                found = True
    except:
        pass

    if not found:
        return None, None

    As = movie_block.find('div', {'class', 'col-9 page-content'}).findAll('a')
    magnets = set()
    for x in As:
        href = x.get('href')
        if href.startswith('magnet:'):
            magnets.add(href)
        elif urllib.parse.urlparse(href).scheme != '':
            if len(href) > len(prefix) and href.startswith(prefix) and prog.match(href[len(prefix):]):
                if not href.endswith('/'):
                    href += '/'
                movieb_data['imdb'] = href[len(prefix):]

    name = str(movie_block.find('div', {'class': 'box-info-heading clearfix'}).text.strip())
    movieb_data['name'] = name
    info = guessit.guessit(name)
    movieb_data['title'] = info['title']

    try:
        movieb_data['seeds'] = str(
            movie_block.find('span', {'class': 'seeds'}).text)
    except:
        movieb_data['seeds'] = None

    try:
        movieb_data['leeches'] = str(
            movie_block.find('span', {'class': 'leeches'}).text)
    except:
        movieb_data['leeches'] = None

    return movieb_data, list(magnets)


def scrape_this(root_url : str, sitemap_file : str):

    pages = []
    if os.path.exists(sitemap_file):
        print("Using existing sitemap file: {}".format(sitemap_file))
        with codecs.open(sitemap_file, 'r', encoding='utf-8') as f:
            for line in f:
                pages.append(line.strip())
    else:
        source = requests.get(urllib.parse.urljoin(root_url, "robots.txt")).text
        url = None
        for line in source.splitlines():
            key, value = line.split(': ')
            if key == 'Sitemap':
                url = value
                break

        to_scrap = []

        source = requests.get(url).text
        soup = bs4.BeautifulSoup(source, 'xml')
        sitemap = soup.findAll('loc')
        for loc in sitemap:
            to_scrap.append(loc.text)

        print("Going over XMLs...")
        for url in random.sample(to_scrap, parser.getint('1337x', 'to_scrap')): #XXX to_scrap
            print(url)
            source = requests.get(url).text
            soup = bs4.BeautifulSoup(source, 'xml')
            sitemap = soup.findAll('loc')
            for loc in sitemap:
                pages.append(loc.text)

        with codecs.open(sitemap_file, 'w', encoding='utf-8') as f:
            for line in pages:
                f.write(line+'\n')

    hash_re = re.compile('btih:([0-9|A-Z|a-z]*)&.*')

    client = pymongo.MongoClient()
    cdb = client['magnets']

    mondb = cdb.magnets
    print("going over {} pages".format(len(pages)))
    err_count = 0
    # for url in pages:
    for url in random.sample(pages, parser.getint('1337x', 'pages')):

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

    print('dup errors: {}'.format(err_count))


scrape_this("https://1337x.to", '1337x.pages.txt')

