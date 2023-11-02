import requests
import os
import json
import urllib.request
import glob
import rasterio
import geopandas as gpd
from rasterio.merge import merge


mosaic_id = '48fff803-4104-49bc-b913-7467b7a5ffb5'
# string_bbox = '-120.071700844924877, 34.678748545451917, -120.01176697920954, 34.743990557604391'
geojson_path = './bounds/geojsons/UCNRS/Sedgwick_Reserve.geojson'

# gets bounding box for a geojson as a string so it can be used with planet API
# also works with a shapefile!
def get_string_bbox(geojson_path):
    gdf = gpd.read_file(geojson_path)
    return str(list(gdf.total_bounds))[1:-1]

string_bbox = get_string_bbox(geojson_path)

# authentication
PLANET_API_KEY = os.getenv('PL_API_KEY')
API_URL = "https://api.planet.com/basemaps/v1/mosaics"
session = requests.Session()
session.auth = (PLANET_API_KEY,'')

# search quads by ROI, store results in a list called "items"
search_parameters = {
    'bbox': string_bbox,
    'minimal': True
}
quads_url = "{}/{}/quads".format(API_URL, mosaic_id)
res = session.get(quads_url, params=search_parameters, stream=True)
# print(json.dumps(res.json(), indent=2))
quads = res.json()
items = quads['items']

# make a new directory to house downloaded quads
if not os.path.exists('quads'):
    os.mkdir('quads')

# loop through results from quads search and download each one as a TIF
for i in items:
    link = i['_links']['download']
    name = i['id']
    name = name + '.tiff'
    DIR = 'quads/' # <= a directory i created, feel free to customize
    filename = os.path.join(DIR, name)
    #checks if file already exists before downloading
    if not os.path.isfile(filename):
        urllib.request.urlretrieve(link, filename)

# mosaic all tiff files in quads folder using rasterio.merge
tif_files = glob.glob(os.path.join('quads', "*.tiff"))
datasets = [rasterio.open(file) for file in tif_files]
mosaic, mosaic_transform = merge(datasets)

# write mosaic to new file
output_name = 'mosaic.tiff'
mosaic_dataset = rasterio.open(
    output_name,
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


# # GARBAGE -- requires a square mosaic
#
# # open those TIFs up
# tif_files = [file for file in os.listdir('quads') if file.endswith(".tif") or file.endswith(".tiff")]
# images = [Image.open(os.path.join('quads', file)) for file in tif_files]
#
#
# width,height = images[0].size   # this assumes all quads are the same size -- should always be 2048x2048
# mosaic_width = width * int(len(images) ** 0.5)
# mosaic_height = height * int(len(images) ** 0.5)
