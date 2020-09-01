import requests
import json

url = "https://unogs-unogs-v1.p.rapidapi.com/aaapi.cgi"
headers = {
    'x-rapidapi-host': "unogs-unogs-v1.p.rapidapi.com",
    'x-rapidapi-key': "KEY"
}

def get_countries():
    querystring = {"t":"lc","q":"available"}

    response = requests.request("GET", url, headers=headers, params=querystring)

    countries = json.loads(response.text)

    c = []
    for country in countries['ITEMS']:
        c.append(country[1].upper())
    return c

def get_chunk(country, page=1, limit=10000):
    querystring = {"q": "get:new%d:%s" % (limit,country,), "p": "%d" %(page,), "t": "ns", "st": "adv"}

    response = requests.request("GET", url, headers=headers, params=querystring)

    chunk = json.loads(response.text)

    return chunk

dict = {}
for country in get_countries():
    chunk = get_chunk(country)
    for item in chunk['ITEMS']:
        dict[item['netflixid']] = item
    count = int(chunk['COUNT'])
    pages = (count-1)//100
    for page in range(pages):
        chunk = get_chunk(country, page+2)
        for item in chunk['ITEMS']:
            dict[item['netflixid']] = item

with open('netflix.json', "w") as f:
    json.dump(dict, f, indent=4)
