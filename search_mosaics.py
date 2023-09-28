import requests
import os
import json

# authentication
PLANET_API_KEY = os.getenv('PL_API_KEY')
API_URL = "https://api.planet.com/basemaps/v1/mosaics"
session = requests.Session()
session.auth = (PLANET_API_KEY,'')

# search for weekly Basemaps
search_params = {
    # 'name__contains' :'monthly'
}
res = session.get(API_URL, params = search_params, stream=True)

print(json.dumps(res.json(), indent=2))
