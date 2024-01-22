### This script takes a directory of mosaics and outputs one or more derived products
### Takes us from L2 to L3



# Directory containing input L1 scenes
mosaic_directory = 'E:/sedgwick_reserve/L2_mosaics'

# Directory to save mosaics to
indices_directory = 'E:/sedgwick_reserve/L3_indices'

# Toggles for derived products to make
make_ndvi = True            # Normalized Difference Vegetation Index
make_evi = True             # Enhanced Vegetation Index
make_ndwi = True            # Normalized Difference Water Index
make_msavi2 = True          # Modified Soil Adjusted Vegetation Index 2
make_mtvi2 = True           # Modified Triangular Vegetation Index 2
make_vari = True            # Visible Atmospherically Resistant Index
make_tgi = True             # Triangular Greenness Index



# Import packages
import datetime
import os
import geopandas as gpd
import rasterio
import json
from rasterio.mask import mask
from rasterio.crs import CRS
import rioxarray as rxr
from rioxarray.merge import merge_arrays
import numpy as np
import xarray as xa


# List all .tif files in the mosaic directory
mosaics = os.listdir(mosaic_directory)
mosaics = [file for file in mosaics if file[-4:] == '.tif']


def get_ndvi(img_path):
    mosaic = rxr.open_rasterio(img_path)
    ndvi = (mosaic.sel(band='NIR') - mosaic.sel(band='R')) / (mosaic.sel(band='NIR') + mosaic.sel(band='R'))
    return ndvi

if make_ndvi:
    # Check if there is an NDVI directory; if not, make one
    if not os.path.exists(os.path.join(indices_directory, 'ndvi')):
        os.mkdir(os.path.join(indices_directory, 'ndvi'))

    # Loop through all mosaics and make an NDVI mosaic for each one
    for mosaic in mosaics:
        print('Making NDVI mosaic for ' + mosaic + '...')
        ndvi = get_ndvi(os.path.join(mosaic_directory, mosaic))
        ndvi.rio.to_raster(os.path.join(indices_directory, 'ndvi', mosaic[:-4] + '_ndvi.tif'))