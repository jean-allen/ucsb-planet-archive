### Reads in a CSV generated by search_scenes.py and orders all images for download to a target directory



# CSV file containing list of image IDs
ids_file_path = 'E:/coal_oil_point/copr_img_ids.csv'

# GeoJSON file containing the AOI; imagery will be clipped to this extent
geojson_path = 'E:/coal_oil_point/Coal_Oil_Point_Natural_Reserve_bb.geojson'

# Directory to download imagery to
output_directory = 'E:/coal_oil_point/L1_harmonized_scenes'



# Import packages
import datetime
import json
import os
import requests
import time
import pandas as pd
from requests.auth import HTTPBasicAuth

# Read in the CSV file containing the list of image IDs
ids_file = pd.read_csv(ids_file_path)
ids = ids_file['Image_IDs'].tolist()

# Read in the AOI file
with open(geojson_path) as f:
    geometry = json.load(f)


# Takes in list of image ID strings, outputs download link
def order_list_of_imgs(id_list, order_name='List of Images Order'):
    # Check which dates we already have imagery for
    original_length = len(id_list)
    existing_files = os.listdir(output_directory)
    existing_datetimes = ['_'.join(file.split('_')[0:2]) for file in existing_files]  # makes list of dates and times for which we already have imagery
    existing_datetimes = list(set(existing_datetimes))  # gets only unique dates and times
    id_list = [id for id in id_list if id[0:15] not in existing_datetimes]
    if len(id_list) < original_length:
        print('Found ' + str(original_length - len(id_list)) + ' images that already exist in the output directory. Skipping...')
    if len(id_list) == 0:
        print('No new images to download. Exiting...')
        return
    if len(id_list) > 500:
        print('Org is limited to 500 bundles per order, but you have ' + str(len(id_list)) + ' images. Splitting into multiple orders...')
        num_orders = int(len(id_list)/500) + 1
        order_links = []
        for i in range(num_orders):
            print('Ordering bundle ' + str(i+1) + ' of ' + str(num_orders) + '...')
            this_order = order_list_of_imgs(id_list[500*i:500*(i+1)], order_name=order_name)
            order_links.append(this_order)
        return order_links
    print('Ordering ' + str(len(id_list)) + ' images...')
    # Order body to be sent over HTTP request
    request_body = {
        "name": order_name,
        "source_type": "scenes",
        "products":[
            {
                "item_ids": id_list,
                "item_type":"PSScene",
                "product_bundle":"analytic_sr_udm2"
            }
        ],
            "tools": [
            {
                "clip": {
                    "aoi": {
                        "type": "Polygon",
                        "coordinates": geometry['features'][0]['geometry']['coordinates']
                    }
                    },         
            },
            {
                "harmonize": {
                    "target_sensor":  "Sentinel-2"
                }, 
            }
            ]
    }
    result = \
        requests.post(
        'https://api.planet.com/compute/ops/orders/v2',
        auth=HTTPBasicAuth(os.environ['PL_API_KEY'], ''),
        json=request_body)
    return [result.json()['_links']['_self']]


# Get the state of an order using the link
# Possible values: queued, running, success, partial, failed, cancelled
def check_on_order(link):
    result = requests.get(link, auth=HTTPBasicAuth(os.environ['PL_API_KEY'], ''))
    return result.json()['state']


# Downloads all scenes at a given search result link to the local directory
def order_all_scenes(link):
    result = requests.get(link, auth=HTTPBasicAuth(os.environ['PL_API_KEY'], '')).json()
    files = result['_links']['results']
    for file in files:
        filename = file['name'].split('/')[-1]
        print(str(datetime.datetime.now().time()) + '    ' + 'Downloading ' + filename + '...')
        r = requests.get(file['location'], auth=HTTPBasicAuth(os.environ['PL_API_KEY'], ''))
        with open(os.path.join(output_directory,filename),'wb') as f:
            f.write(r.content)

# Waits for an order to be ready and then starts downloading imagery
def download_order(link):
    result = requests.get(link, auth=HTTPBasicAuth(os.environ['PL_API_KEY'], ''))
    state = result.json()['state']
    isDone = False
    while isDone==False:
        if state=='queued':
            print(str(datetime.datetime.now().time()) + '    ' + 'Order queued. Waiting for processing to begin...')
            time.sleep(1)
            result = requests.get(link, auth=HTTPBasicAuth(os.environ['PL_API_KEY'], ''))
            state = result.json()['state']
        elif state=='running':
            try:
                result = requests.get(link, auth=HTTPBasicAuth(os.environ['PL_API_KEY'], ''))
                print(str(datetime.datetime.now().time()) + '    ' + str(result.json()['last_message'])+'...')
            except KeyError: # sometimes state isn't in the returned json for some reason
                print(str(datetime.datetime.now().time()) + '    ' + 'Order running...')
                time.sleep(4)
                continue
            state = result.json()['state']
            time.sleep(5)
        elif state=='success':
            print(str(datetime.datetime.now().time()) + '    ' + 'All scenes processed successfully. Now beginning download...')
            order_all_scenes(link)
            isDone=True
        elif state=='partial':
            print(str(datetime.datetime.now().time()) + '    ' + 'Some scenes failed to process. Exiting...')
            isDone=True
        elif state=='failed':
            print(str(datetime.datetime.now().time()) + '    ' + 'Order failed. Exiting...')
            isDone=True
        elif state=='cancelled':
            print(str(datetime.datetime.now().time()) + '    ' + 'Order cancelled. Exiting...')
            isDone=True

# Check if output directory exists; if not, make it
if not os.path.exists(output_directory):
    os.makedirs(output_directory)

# Liftoff!
list_of_download_links = order_list_of_imgs(ids)
print(str(len(list_of_download_links)) + ' orders created.')
if len(list_of_download_links) > 1:
    print('This is going to take a while O_O')
if len(list_of_download_links) > 3:
    print('Like, a REALLY LONG while...')

for count, link in enumerate(list_of_download_links):
    print(str(datetime.datetime.now().time()) + '    STARTING ORDER #' + str(count+1) + ' OF ' + str(len(list_of_download_links)))
    download_order(link[0])