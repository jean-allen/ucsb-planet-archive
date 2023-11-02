import requests
import os
import json
import pandas

# authentication
PLANET_API_KEY = os.getenv('PL_API_KEY')
API_URL = "https://api.planet.com/basemaps/v1/mosaics"
session = requests.Session()
session.auth = (PLANET_API_KEY,'')

# get all mosaics
res = session.get(API_URL, stream=True)
# print(json.dumps(res.json(), indent=2))

# takes a mosaic and stores the important info in a tuple
def getMosaicInfo(mosaic):
    # links
    self_link = mosaic['_links']['_self']
    quads_link = mosaic['_links']['quads']
    tiles_link = mosaic['_links']['tiles']

    id = mosaic['id']
    interval = mosaic['interval']
    bbox = mosaic['bbox']
    name = mosaic['name']
    products = mosaic['item_types']
    return (name, id, interval, products, bbox, self_link, quads_link, tiles_link)

# adds important mosaic info to list of results
def handle_page(page):
    for item in page["mosaics"]:
        results.append(getMosaicInfo(item))

# pagination
def fetch_page(search_url):
    page = session.get(search_url).json()
    handle_page(page)
    next_url = page["_links"].get("_next")
    if next_url:
        fetch_page(next_url)

results = []
search_url = res.json()['_links']['_self']
fetch_page(search_url)
titles = ['name', 'id', 'interval', 'products', 'bbox', 'self_link', 'quads_link', 'tiles_link']
pandas.DataFrame(results, columns = titles).to_csv('all_mosaics.csv')
