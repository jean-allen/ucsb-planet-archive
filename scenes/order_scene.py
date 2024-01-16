import datetime
import json
import os
import requests
import time
from requests.auth import HTTPBasicAuth

# This is the image ID of the image we want to download
this_img = '20210901_180754_0f4e_3B_AnalyticMS_SR_clip.tif'

# Takes in image ID string, outputs download link
def order_img(img_id, order_name='Single Image Order'):
    # Order body to be sent over HTTP request
    request_body = {
       "name": order_name,
       "source_type": "scenes",
       "products":[
          {
             "item_ids":[img_id],
             "item_type":"PSScene",
             "product_bundle":"analytic_sr_udm2"
          }
       ]
    }
    result = \
      requests.post(
        'https://api.planet.com/compute/ops/orders/v2',
        auth=HTTPBasicAuth(os.environ['PL_API_KEY'], ''),
        json=request_body)
    return result.json()['_links']['_self']


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
        print('Downloading ' + filename + '...')
        r = requests.get(file['location'], auth=HTTPBasicAuth(os.environ['PL_API_KEY'], ''))
        with open(filename,'wb') as f:
            f.write(r.content)

# Waits for an order to be ready and then starts downloading imagery
def download_order(link):
    result = requests.get(link, auth=HTTPBasicAuth(os.environ['PL_API_KEY'], ''))
    state = result.json()['state']
    isDone = False
    while isDone==False:
        if state=='queued':
            time.sleep(1)
            result = requests.get(link, auth=HTTPBasicAuth(os.environ['PL_API_KEY'], ''))
            state = result.json()['state']
        elif state=='running':
            try:
                result = requests.get(link, auth=HTTPBasicAuth(os.environ['PL_API_KEY'], ''))
                print(datetime.datetime.now().time(), '  ', str(result.json()['last_message'])+'...')
            except KeyError: # sometimes state isn't in the returned json for some reason
                time.sleep(5)
                continue
            state = result.json()['state']
            time.sleep(5)
        elif state=='success':
            print('All scenes processed successfully. Now beginning download...')
            order_all_scenes(link)
            isDone=True
        elif state=='partial':
            isDone=True
        elif state=='failed':
            isDone=True
        elif state=='cancelled':
            isDone=True


# Liftoff!
this_link = order_img(this_img)
download_order(this_link)
