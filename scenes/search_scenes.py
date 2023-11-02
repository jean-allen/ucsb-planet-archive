geojson_path = './bounds/geojsons_bb/UCNRS/Sedgwick_Reserve_bb.geojson'


import requests
import os
import json
import urllib.request
import glob
import rasterio
import shutil
import geopandas as gpd
from rasterio.merge import merge
import json
from requests.auth import HTTPBasicAuth


# authentication
PLANET_API_KEY = os.getenv('PL_API_KEY')
API_URL = "https://api.planet.com/basemaps/v1/mosaics"
session = requests.Session()
session.auth = (PLANET_API_KEY,'')


# filter for items the overlap with our chosen geometry
with open(geojson_path) as f:
    geometry = json.load(f)

geometry_filter = {
    "type": "GeometryFilter",
    "field_name": "geometry",
    "config": {
        "type": "Polygon",
        "coordinates": geometry['features'][0]['geometry']['coordinates']
    }
}


# # filter images acquired in a certain date range
# date_range_filter = {
#   "type": "DateRangeFilter",
#   "field_name": "acquired",
#   "config": {
#     "gte": "2016-01-01T00:00:00.000Z",
#     "lte": "2017-01-01T00:00:00.000Z"
#   }
# }


# filter any images which are more than 50% clouds
cloud_cover_filter = {
  "type": "RangeFilter",
  "field_name": "cloud_cover",
  "config": {
    "lte": 0.5
  }
}

# filter any images where the orthorectified 4b SR image is not available
type_filter = {
    "type": "AssetFilter",
    "config": [
        "ortho_analytic_4b_sr"
    ]
}


# mash 'em all together
big_filter = {
  "type": "AndFilter",
  "config": [geometry_filter, type_filter, cloud_cover_filter]
}



# Search API request object
search_endpoint_request = {
  "item_types": ["PSScene"],
  "filter": big_filter
}

result = \
  requests.post(
    'https://api.planet.com/data/v1/quick-search',
    auth=HTTPBasicAuth(os.environ['PL_API_KEY'], ''),
    json=search_endpoint_request)



# adds image ids to list of results
def handle_page(page):
    for item in page["features"]:
        item_ids.append(item['id'])
        # print(item['id'])

# pagination
def fetch_page(search_url):
    page = session.get(search_url).json()
    handle_page(page)
    next_url = page["_links"].get("_next")
    if next_url:
        fetch_page(next_url)

# stores all image ids in a list
item_ids = []
search_url = result.json()['_links']['_self']
fetch_page(search_url)

# dumps img ids to a text file
with open('all_img_ids.txt', 'w') as f:
    for line in item_ids:
        f.write(f"{line}\n")
