### Gets list of images that overlap with a given date, collects relevant metadata, and dumps it all to a csv



geojson_path = './bounds/geojsons/UCNRS/Sedgwick_Reserve.geojson'
output_file = './sedgwick_img_ids.csv'


import requests
import os
import json
import pandas as pd
import numpy as np
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
        dates.append(item['properties']['acquired'])
        try:
            visible_percents.append(item['properties']['visible_percent'])
        except:
            visible_percents.append(np.NaN)
        ground_controls.append(item['properties']['ground_control'])
        satellite_azimuths.append(item['properties']['satellite_azimuth'])
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
dates = []
visible_percents = []
ground_controls = []
satellite_azimuths = []

search_url = result.json()['_links']['_self']
fetch_page(search_url)

# store img metadata in a dataframe
outputs = {
    'Image_IDs': item_ids,
    'Datetime': dates,
    'Visible_Percent': visible_percents,
    'Ground_Control': ground_controls,
    'Satellite_Azimuth': satellite_azimuths
}
df = pd.DataFrame(outputs)

# some quick QOL adjustments...
df['Date'] = df['Datetime'].str[:10]
df['Time_UTC'] = df['Datetime'].str[11:-1]
df = df.drop('Datetime', axis=1)


# save outputs to csv
df.to_csv(output_file, index=False)
