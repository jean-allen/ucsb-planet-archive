### Collects full monthly basemap imagery dataset for an ROI defined by a geojson


geojson_path = './bounds/geojsons/UCNRS/Sedgwick_Reserve.geojson'


import requests
import os
import json
import urllib.request
import glob
import rasterio
import shutil
import geopandas as gpd
from rasterio.merge import merge


# authentication
PLANET_API_KEY = os.getenv('PL_API_KEY')
API_URL = "https://api.planet.com/basemaps/v1/mosaics"
session = requests.Session()
session.auth = (PLANET_API_KEY,'')


# get bounding box for ROI
def get_string_bbox(geojson_path):
    gdf = gpd.read_file(geojson_path)
    return str(list(gdf.total_bounds))[1:-1]


string_bbox = get_string_bbox(geojson_path)

# make list of IDs of basemaps in the 4-band monthly basemap datasets
# note -- at time of writing, there's an issue in the Planet API where the "_self" link in search results
# doesn't account for any search parameters used on the dataset. to get around that, I make a list of all
# the basemaps and filter them on my own.
res = session.get(API_URL, stream=True)

# adds important mosaic info to list of results
def handle_page(page):
    for item in page["mosaics"]:
        if 'ps_monthly_normalized_' in item['name']:
            desiredBasemaps.append((item['name'], item['id'], item['bbox']))

# pagination
def fetch_page(search_url):
    page = session.get(search_url).json()
    handle_page(page)
    next_url = page["_links"].get("_next")
    if next_url:
        fetch_page(next_url)

desiredBasemaps = []
search_url = res.json()['_links']['_self']
fetch_page(search_url)



# downloads all quads within an ROI and stores them in a directory
def downloadQuads(mosaic_id, bbox, output_prefix):
    search_parameters = {'bbox': bbox, 'minimal': True}
    quads_url = "{}/{}/quads".format("https://api.planet.com/basemaps/v1/mosaics", mosaic_id)
    quads_request = session.get(quads_url, params=search_parameters, stream=True)
    print(quads_request)
    quads = quads_request.json()['items']
    if not os.path.exists(output_prefix + '_quads'):
        os.mkdir(output_prefix + '_quads')
    for i in quads:
        link = i['_links']['download']
        name = i['id']
        name = output_prefix + '_' + name + '.tiff'
        DIR = output_prefix + '_quads/' # <= a directory i created, feel free to customize
        filename = os.path.join(DIR, name)
        #checks if file already exists before downloading
        if not os.path.isfile(filename):
            urllib.request.urlretrieve(link, filename)


# takes every tiff file in a directory and mosaics them together into a new tiff file
def make_mosaic(directory, output_name):
    tif_files = glob.glob(os.path.join(directory, "*.tiff"))
    # if len(tif_files )
    datasets = [rasterio.open(file) for file in tif_files]
    mosaic, mosaic_transform = merge(datasets)
    mosaic_dataset = rasterio.open(
        output_name + '.tiff',
        "w",
        driver="GTiff",
        height=mosaic.shape[1],
        width=mosaic.shape[2],
        count=mosaic.shape[0],
        dtype=mosaic.dtype,
        crs=datasets[0].crs,
        transform=mosaic_transform,
    )
    mosaic_dataset.write(mosaic)


for name, id, bbox in desiredBasemaps:
    date = name[-14:-7]
    downloadQuads(id, string_bbox, date)

for name, id in desiredBasemaps:
    date = name[-14:-7]
    make_mosaic(date + '_quads', './mosaics/Sedgwick_' + date)
    shutil.rmtree(date+'_quads')
