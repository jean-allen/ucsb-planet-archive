import os
import geopandas as gpd
import rasterio
from rasterio.merge import merge
from rasterio.io import MemoryFile
from rasterio.warp import reproject, Resampling
from rasterio.mask import mask
from rasterio.crs import CRS
from datetime import datetime, timedelta
import rioxarray as rxr
from rioxarray.merge import merge_arrays
from glob import glob
import numpy as np
import xarray as xa
from arosics import COREG

## TEST

# Shapefile of the place you're building an NDVI stack for
shapefile = 'Sedgwick_Reserve.geojson'
imagery_directory = './imagery_clipped_harmonized'

gdf = gpd.read_file(shapefile).to_crs(epsg=32610)





# takes an image and a geodataframe and saves out a cropped TIF
def clip_file(img, gdf, output_file_name):
    with rasterio.open(img) as src:
        try:
            clipped, transform = mask(src, gdf.geometry, crop=True)
            with rasterio.open(output_file_name, "w", driver='GTiff', width=clipped.shape[2], height=clipped.shape[1], count=clipped.shape[0], dtype=clipped.dtype, crs=src.crs, transform=transform) as dest:
                dest.write(clipped)
        except ValueError:
            print('No sausage')

# takes a list of file paths and outputs a mosaic of all those files
def make_mosaic(list_of_imgs, output_file_name, dst_epsg, clip_gdf):

    dst_crs = CRS.from_string('EPSG:' + str(dst_epsg))
    gdf_crs = clip_gdf.to_crs(dst_crs)
    # Open all images in the list and reproject them to the target CRS
    imgs = []
    for file in list_of_imgs:
        this_img = rxr.open_rasterio(os.path.join(imagery_directory, file))
        if (this_img.rio.crs != dst_crs):
            this_img = this_img.rio.reproject(dst_crs)
        imgs.append(this_img)

    # Check percentage overlap between the polygon and the rasters
    # This process minimizes seam lines -- scenes that cover more of the ROI will be prioritized
    polygon = gdf_crs.geometry.iloc[0]
    num_pixels = []
    for raster in imgs:
        mask = rasterio.features.geometry_mask([gdf.iloc[0].geometry],
                                               out_shape=raster.shape[-2:],
                                               transform=raster.rio.transform(),
                                               invert=True)
        num_pixels.append(np.sum(mask))

    # Sort imgs bassed on how many pixels they have that overlaps with the GDF
    # merge_arrays uses a reverse painters algorithm to make the mosaic, so they need to be in the correct order
    imgs_sorted = [x for _,x in sorted(zip(num_pixels, imgs), key=lambda pair:pair[0])]

    # # Calculate NDVI for each img
    # ndvis = []
    # for img in imgs_sorted:
    #     nir = img[3,:,:]
    #     red = img[2,:,:]
    #     ndvi = (nir - red) / (nir + red)
    #     ndvis.append(ndvi)

    # Make mosaic...
    this_mosaic = merge_arrays(imgs_sorted)

    # Convert DataArray to Dataset so that we can save out the multi-band rasters
    bands = ['R', 'G', 'B', 'NIR']
    output = xa.Dataset()
    for bandnum, band in enumerate(bands):
        output[band] = this_mosaic[bandnum,:,:]

    output.rio.to_raster(output_file_name)

    # output_profile = this_img.profile
    # output_profile.update(
    #     width=this_mosaic.shape[2],
    #     height=this_mosaic.shape[1],
    #     count=len(this_mosaic),
    #     dtype=str(this_mosaic.dtype),
    #     transform=mosaic_transform)
    #
    # with rasterio.open(output_file_name, 'w', **output_profile) as dst:
    #     dst.write(this_mosaic.astype(this_mosaic.dtype))
    #
    # for img in imgs:
    #     img.close()

    # del imgs
    # del this_mosaic

# Calculates and saves out an NDVI image
def ndvi_planet(img_path,output_path):
    with rasterio.open(img_path) as src:
        band3 = src.read(3)
        band4 = src.read(4)

        ndvi = (band4 - band3) / (band4 + band3)

        profile = src.profile
        profile.update(dtype=rasterio.float32,count=1)

        with rasterio.open(output_path, 'w', **profile) as dst:
            dst.write(ndvi, 1)

# Coregisters with arosics and aligns raster extents
# im_ref is the path to the reference file, im_tar is the path to the one that will be edited
def coregister_imgs(im_ref, im_tar, output_path):
    try:
        CR = COREG(im_ref, im_tar, align_grids=True, path_out=output_path, fmt_out='GTIFF', resamp_alg_deshift='nearest')
        CR.correct_shifts()
    except RuntimeError:
        print('whoopsie daisy')

# # Makes a layer stack of all files in a directory
# # under construction...
# def layer_stack(dir, desired_epsg):
#     file_path = os.path.join(dir, '*.tif')
#     stack_files = glob(file_path)
#     for file in stack_files:
#         one_file = rxr.open_rasterio(file)
#         if one_file.rio.crs=='EPSG:32610':

# reprojects all files in a directory to have the same crs
# under construction...
# def align_all_projections(input_dir, output_dir, dst_epsg):
#     dst_crs = CRS.from_string('EPSG:' + str(dst_epsg))
#
#     output_dir = os.path.join("data", "outputs")
#     if os.path.isdir(output_dir) == False:
#         os.mkdir(output_dir)
#
#     file_path = os.path.join(dir, '*.tif')
#     stack_files = glob(file_path)
#     for file in stack_files:
#         one_file = rxr.open_rasterio(file)
#         if (one_file.rio.crs=='EPSG:'+str(dst_epsg)):



# lists out SR images in the directory
all_imgs = [filename for filename in os.listdir(imagery_directory) if filename.endswith('harmonized_clip.tif')]



# Lists dates that we're getting mosaics for
start_date = datetime(2022, 1, 1)
end_date = datetime(2022, 12, 31)
date_list = []
while start_date <= end_date:
    date_list.append(start_date.strftime('%Y%m%d'))
    start_date += timedelta(days=1)

print('Start making mosaics...')

# make mosaics for all dates in date_list
if not os.path.exists('mosaics'):
    os.makedirs('mosaics')

for date in date_list:
    print('Working on ' + date + '...')
    this_date_files = [filename for filename in os.listdir(imagery_directory) if filename.startswith(date)]
    if len(this_date_files)==0:
        continue
    this_date_images = [filename for filename in this_date_files if filename.endswith('harmonized_clip.tif')]
    # make_mosaic(this_date_images, './mosaics/' + date + '.tif', 32610, gdf)

mosaic_list = os.listdir('./mosaics')

print('Done making mosaics. Start NDVI calculation...')

# NDVI Calculation
if not os.path.exists('mosaics_ndvi'):
    os.makedirs('mosaics_ndvi')
for mosaic in mosaic_list:
    print('Working on '+mosaic+'...')
    # ndvi_planet('./mosaics/'+mosaic,mosaic[:-4]+'_ndvi.tif')

print('Done calculating NDVI. Start coregistration...')

if not os.path.exists('mosaics_ndvi_coregistered'):
    os.makedirs('mosaics_ndvi_coregistered')

ndvi_list = os.listdir('./mosaics_ndvi')
ref_img = ndvi_list[0]

for file in ndvi_list:
    coregister_imgs('./mosaics_ndvi/'+ref_img, './mosaics_ndvi/'+file, './mosaics_ndvi_coregistered/' + file[:-4] + '_coreg.tif')
