### This script takes a directory of PlanetScope scenes and makes a mosaic of all the scenes for a given day
### Takes us from L1 to L2



# Directory containing input L1 scenes
imagery_directory = 'E:/sedgwick_reserve/L1_harmonized_scenes'

# Directory to save mosaics to
output_directory = 'E:/sedgwick_reserve/L2_mosaics'

# GeoJSON of the place you're building an NDVI stack for
input_geojson = 'E:/sedgwick_reserve/Sedgwick_Reserve.geojson'

# Desired EPSG code of the output mosaic
dst_epsg = 32610



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


# Read in the GeoJSON file; this will be used in the mosaic function
gdf = gpd.read_file(input_geojson).to_crs(epsg=32610)

# takes an image and a udm2 open in rioxarray and applies the udm2 to the image using band 1 (clear/not-clear)
def apply_udm2(img, udm):
    img_masked = img.where(udm[0,:,:]==1, other=np.nan)
    return img_masked

# takes a list of file paths and outputs a mosaic of all those files
# list of images: list of file paths to images
# output_file_name: file path to save the mosaic to
# dst_epsg: desired EPSG code of the output mosaic
# clip_gdf: geodataframe to clip the mosaic to
def make_mosaic(list_of_imgs, output_file_name, epsg, clip_gdf):

    # Sometimes images come in different CRS's -- this will put them all in the same one
    dst_crs = CRS.from_string('EPSG:' + str(epsg))      # convert EPSG to CRS object
    gdf_crs = clip_gdf.to_crs(dst_crs)            # reproject the input geometry to the target CRS

    # Open all images in the list and reproject them to the target CRS
    imgs = []
    for file in list_of_imgs:
        this_img = rxr.open_rasterio(os.path.join(imagery_directory, file))
        if (this_img.rio.crs != dst_crs):
            this_img = this_img.rio.reproject(dst_crs)
        udm_path = file.split('3B')[0] + '3B_udm2_clip.tif'     # 3B is the code for the analytic SR data product
        this_udm = rxr.open_rasterio(os.path.join(imagery_directory, udm_path))
        if (this_udm.rio.crs != dst_crs):
            this_udm = this_udm.rio.reproject(dst_crs)
        imgs.append(apply_udm2(this_img, this_udm))

    # Check percentage overlap between the polygon and the rasters
    # This process minimizes seam lines -- scenes that cover more of the ROI will be prioritized over scenes that cover less
    polygon = gdf_crs.geometry.iloc[0]
    num_pixels = []
    for raster in imgs:
        # Counts pixels that overlap with the polygon
        num_pixels.append(np.count_nonzero(raster.rio.clip([polygon], gdf_crs.crs, drop=False).values[0,:,:]))

    # Sort imgs bassed on how many pixels they have that overlaps with the GDF
    # merge_arrays uses a reverse painters algorithm to make the mosaic, so they need to be in the correct order
    imgs_sorted = [x for _,x in sorted(zip(num_pixels, imgs), key=lambda pair:pair[0])]
    imgs_sorted.reverse()

    # Make mosaic...
    this_mosaic = merge_arrays(imgs_sorted, nodata=np.nan)

    # Convert DataArray to Dataset so that we can save out the multi-band rasters
    bands = ['R', 'G', 'B', 'NIR']
    output = xa.Dataset()
    for bandnum, band in enumerate(bands):
        output[band] = this_mosaic[bandnum,:,:]

    output.rio.to_raster(output_file_name)



# lists out SR images in the input directory
all_imgs = [filename for filename in os.listdir(imagery_directory) if filename.endswith('harmonized_clip.tif')]

# list out dates that we have imagery for
dates = [filename.split('_')[0] for filename in all_imgs]
dates = list(set(dates))



# Check which dates we already have mosaics for
if not os.path.exists(output_directory):
    os.makedirs(output_directory)
existing_files = os.listdir(output_directory)
existing_dates = [file.split('.')[0] for file in existing_files]
existing_dates = list(set(existing_dates))
date_list = [date for date in dates if date not in existing_dates]

if len(date_list) == 0:
    print('No new dates to make mosaics for. Exiting...')
    exit()
if len(date_list) == len(dates):
    print('Making mosaics for ' + str(len(date_list)) + ' dates...')
else:
    print('Skipping ' + str(len(dates) - len(date_list)) + ' dates that already have mosaics. Making mosaics for ' + str(len(date_list)) + ' dates...')

# make mosaics for all dates in date_list
for date in date_list:
    print('Working on ' + date + '...')
    # filter out images that aren't from this date
    this_date_files = [filename for filename in os.listdir(imagery_directory) if filename.startswith(date)]
    if len(this_date_files)==0:
        continue
    # get only the SR images
    this_date_images = [os.path.join(imagery_directory,filename) for filename in this_date_files if filename.endswith('harmonized_clip.tif')]
    # make the mosaic
    make_mosaic(this_date_images, os.path.join(output_directory, date + '.tif'), dst_epsg, gdf)
    # save out metadata to a json file
    metadata_dict = {
        'created': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'source_dir': imagery_directory,
        'scenes': this_date_images,
        'epsg': dst_epsg,
        'geojson_used': input_geojson
        }
    with open(os.path.join(output_directory, date + '_metadata.json'), 'w') as outfile:
        json.dump(metadata_dict, outfile)


