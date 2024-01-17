### Gets list of images that overlap with a given date, collects relevant metadata, and dumps it all to a csv



geojson_path = './bounds/geojsons/seki.json'
output_file = './seki_img_ids_2016.csv'



import requests
import os
import json
import pandas as pd
import numpy as np
import time
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


# filter images acquired in a certain date range
# if a date range filter is added, make sure to add it to "big_filter" below
date_range_filter = {
  "type": "DateRangeFilter",
  "field_name": "acquired",
  "config": {
    "gte": "2016-01-01T00:00:00.000Z",
    "lte": "2017-01-01T00:00:00.000Z"
  }
}


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
  "config": [geometry_filter, type_filter, cloud_cover_filter, date_range_filter]
}



# Search API request object
search_endpoint_request = {
  "item_types": ["PSScene"],
  "filter": big_filter
}

# fire off the POST request
print('Searching...')
result = \
  requests.post(
    'https://api.planet.com/data/v1/quick-search',
    auth=HTTPBasicAuth(os.environ['PL_API_KEY'], ''),
    json=search_endpoint_request)
print(result.status_code, result.reason)




# handling for 413 'Request Entity Too Large' HTTP error
if result.status_code == 413:
    while True:
        print('A 413 error is usually caused by having too many points in the geometry.')
        print('The existing geometry has ' + str(len(geometry['features'][0]['geometry']['coordinates'][0])) + ' points.')
        print('Reducing detail in the geometry and trying again...')
        
        # removes every other point on the input geometry to reduce the size of the request body
        # this will reduce the detail of the geometry, but it will still be roughly the same shape
        all_points = geometry['features'][0]['geometry']['coordinates'][0]
        new_points = []
        for i in range(0, len(all_points), 2):
            new_points.append(all_points[i])

        geometry['features'][0]['geometry']['coordinates'][0] = new_points

        geometry_filter = {
            "type": "GeometryFilter",
            "field_name": "geometry",
            "config": {
                "type": "Polygon",
                "coordinates": geometry['features'][0]['geometry']['coordinates']
            }
        }

        big_filter = {
        "type": "AndFilter",
        "config": [geometry_filter, type_filter, cloud_cover_filter]
        }
        search_endpoint_request = {
        "item_types": ["PSScene"],
        "filter": big_filter
        }
        result = \
        requests.post(
            'https://api.planet.com/data/v1/quick-search',
            auth=HTTPBasicAuth(os.environ['PL_API_KEY'], ''),
            json=search_endpoint_request)
        print(result.status_code, result.reason)
        if result.status_code != 413:
            print("Request successful with " + str(len(geometry['features'][0]['geometry']['coordinates'][0])) + " points.")
            break
        if result.status_code == 413:
            print("Reduced geometry still too large. Trying again...")
            time.sleep(1)   ### this is a hacky way to avoid getting rate limited by the API
            continue



# stores all image ids in a list
item_ids = []
dates = []
visible_percents = []
ground_controls = []
satellite_azimuths = []

print("Fetching results...")
search_url = result.json()['_links']['_self']



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


# pagination
def fetch_page(search_url):
    fetch_page.counter += 1
    print("Working on page " + str(fetch_page.counter) + " of results...")
    page = session.get(search_url).json()
    handle_page(page)
    next_url = page["_links"].get("_next")
    if next_url:
        fetch_page(next_url)

# let's go!
fetch_page.counter = 0
fetch_page(search_url)

# store img metadata in a dataframe
outputs = {
    'Image_IDs': item_ids,
    'Datetime': dates,
    'Visible_Percent': visible_percents,
    'Ground_Control': ground_controls,
    'Satellite_Azimuth': satellite_azimuths
}
print("Search complete. Saving results to disk...")
df = pd.DataFrame(outputs)


# some quick QOL adjustments...
df['Date'] = df['Datetime'].str[:10]
df['Time_UTC'] = df['Datetime'].str[11:-1]
df = df.sort_values(by=['Datetime'])
df = df.drop('Datetime', axis=1)


# save outputs to csv
df.to_csv(output_file, index=False)
print("Done.")