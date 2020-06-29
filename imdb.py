import bs4
import requests
import time
import random
import re
import pymongo
import help_routines
from configparser import ConfigParser

parser = ConfigParser()
parser.read('config.ini')

def scrape_mblock(imdb_type : str, movie_block : bs4.element.Tag):
    movieb_data = {'type': imdb_type}

    try:
        movieb_data['name'] = movie_block.find('a').get_text()  # Name of the movie
        movieb_data['href'] = movie_block.find('a').get('href')
    except:
        movieb_data['name'] = None

    try:
        movieb_data['year'] = str(
            movie_block.find('span', {'class': 'lister-item-year'}).contents[0][1:-1])  # Release year
    except:
        movieb_data['year'] = None

    try:
        movieb_data['rating'] = float(
            movie_block.find('div', {'class': 'inline-block ratings-imdb-rating'}).get('data-value'))  # rating
    except:
        movieb_data['rating'] = None

    try:
        movieb_data['votes'] = int(movie_block.find('span', {'name': 'nv'}).get('data-value'))  # votes
    except:
        movieb_data['votes'] = None

    return movieb_data


def scrape_m_page(imdb_type : str, movie_blocks : bs4.ResultSet):
    page_movie_data = []

    for block in movie_blocks:
        page_movie_data.append(scrape_mblock(imdb_type, block))

    return page_movie_data


def scrape_this(imdb_type: str, link: str, t_count : int):

    base_url = link
    target = t_count

    current_mcount_end = 0
    remaining_mcount = target - current_mcount_end

    movie_data = []

    url = base_url

    while remaining_mcount > 0:

        source = requests.get(url).text
        soup = bs4.BeautifulSoup(source, 'html.parser')

        movie_blocks = soup.findAll('div', {'class': 'lister-item-content'})

        movie_data.extend(scrape_m_page(imdb_type, movie_blocks))

        current_mcount_start = int(
            soup.find("div", {"class": "nav"}).find("div", 
                        {"class": "desc"}).contents[1].get_text().split("-")[0].replace(',', ''))

        current_mcount_end = int(
            soup.find("div", {"class": "nav"}).find("div", {"class": "desc"}).contents[1].get_text().split("-")[
                1].split(" ")[0].replace(',', ''))

        remaining_mcount = target - current_mcount_end

        print("\rcurrently scraping movies from: {} - {} | remaining count: {}".format(
                        current_mcount_start, current_mcount_end, remaining_mcount), 
                        flush=True, end="")

        url = "https://www.imdb.com" + soup.find('div', 
                    {'class': 'desc'}).find('a', class_='lister-page-next next-page').get('href')

        time.sleep(random.randint(0, 10))

    return movie_data

def load_imdb(mondb : pymongo.collection.Collection, secdb: pymongo.collection.Collection, j):
    prog = re.compile("^/title/(tt[0-9]+)(/)?$")
    imdb = []
    id = 0
    for item in j:
        id += 1
        title = item['name'].lower()
        if title in imdb:
            print('duplicate', item)
            continue
        m = prog.search(item['href'])
        dbid = m.group(1)
        imdb.append({
            '_id': dbid,
            'title': item['name'],
            'href': item['href'],
            'year': item['year'],
            'rating': item['rating'],
            'votes': item['votes'],
            'type': item['type'],
            'id': id,
        })

    err_count = 0
    for data in imdb:
        try:
            mondb.insert_one(data)
            sec = {
                '_id': help_routines.fix_name(data['title']),
                'dbid': data['_id'],
            }
            secdb.insert_one(sec)
        except pymongo.errors.DuplicateKeyError:
            err_count += 1

    print('dup errors: {}'.format(err_count))

def main():
    client = pymongo.MongoClient()
    cdb = client['imdb']

    mondb=cdb.imdb
    mondb.drop()
    monsectvdb=cdb.sectvdb
    monsectvdb.drop()
    monsecmoviedb=cdb.secmoviedb
    monsecmoviedb.drop()

    base_scraping_link = "https://www.imdb.com/search/title/?title_type=movies&num_votes=2,&sort=num_votes,desc&count=200"

    films = scrape_this('Movie', base_scraping_link, parser.getint('imdb', 'top_movies'))

    load_imdb(mondb, monsecmoviedb, films)

    base_scraping_link = "https://www.imdb.com/search/title/?title_type=tv_series&num_votes=2,&sort=num_votes,desc&count=200"

    tvshows = scrape_this('TVSeries', base_scraping_link, parser.getint('imdb', 'top_tvseries'))

    load_imdb(mondb, monsectvdb, tvshows)

if __name__ == '__main__':
    main()
