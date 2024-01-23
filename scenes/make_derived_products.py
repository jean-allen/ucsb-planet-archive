### This script takes a directory of mosaics and outputs one or more of a list of derived products
### Takes us from L2 to L3



# Directory containing input L1 scenes
mosaic_directory = 'E:/sedgwick_reserve/L2_mosaics'

# Directory to save mosaics to
indices_directory = 'E:/sedgwick_reserve/L3_indices'

# Toggles for derived products to make
make_ndvi = True            # Normalized Difference Vegetation Index
make_ndwi = True            # Normalized Difference Water Index
make_msavi2 = True          # Modified Soil Adjusted Vegetation Index 2
make_mtvi2 = True           # Modified Triangular Vegetation Index 2
make_vari = True            # Visible Atmospherically Resistant Index
make_tgi = True             # Triangular Greenness Index



# Import packages
import os
import rioxarray as rxr


# List all .tif files in the mosaic directory
mosaics = os.listdir(mosaic_directory)
mosaics = [file for file in mosaics if file[-4:] == '.tif']




#### Index functions ####
#### All equations were taken from Planet's developer tool website: https://developers.planet.com/docs/basemaps/tile-services/indices/#remote-sensing-indices-legends"



# NDVI: Normalized Difference Vegetation Index
def get_ndvi(img_path):
    mosaic = rxr.open_rasterio(img_path)
    red = mosaic.sel(band=3)
    nir = mosaic.sel(band=4)
    ndvi = (nir - red) / (nir + red)
    return ndvi

# NDWI: Normalized Difference Water Index
# NOTE: This is the version of NDWI that uses green and NIR bands, NOT the version that uses SWIR bands
def get_ndwi(img_path):
    mosaic = rxr.open_rasterio(img_path)
    green = mosaic.sel(band=2)
    nir = mosaic.sel(band=4)
    ndwi = (green - nir) / (green + nir)
    return ndwi

# MSAVI2: Modified Soil Adjusted Vegetation Index 2
def get_msavi2(img_path):
    mosaic = rxr.open_rasterio(img_path)
    red = mosaic.sel(band=3)
    nir = mosaic.sel(band=4)
    msavi2 = (2*nir + 1 - ((2*nir + 1)**2 - 8*(nir - red))**0.5) / 2
    return msavi2

# MTVI2: Modified Triangular Vegetation Index 2
def get_mtvi2(img_path):
    mosaic = rxr.open_rasterio(img_path)
    green = mosaic.sel(band=2)
    red = mosaic.sel(band=3)
    nir = mosaic.sel(band=4)
    mtvi2 = 1.5 * (1.2 * (nir - green) - 2.5 * (red - green)) / (((2*nir+1)**2 - (6*nir-5*(red)**0.5))**0.5-0.5)
    return mtvi2

# VARI: Visible Atmospherically Resistant Index
def get_vari(img_path):
    mosaic = rxr.open_rasterio(img_path)
    blue = mosaic.sel(band=1)
    green = mosaic.sel(band=2)
    red = mosaic.sel(band=3)
    vari = (green - red) / (green + red - blue)
    return vari

# TGI: Triangular Greenness Index
def get_tgi(img_path):
    mosaic = rxr.open_rasterio(img_path)
    blue = mosaic.sel(band=1)
    green = mosaic.sel(band=2)
    red = mosaic.sel(band=3)
    tgi = (120*(red-blue)-(190*(red-green))) / (2)
    return tgi





#### Make derived products ####

# NDVI: Normalized Difference Vegetation Index
if make_ndvi:
    # Check if there is an NDVI directory; if not, make one
    if not os.path.exists(os.path.join(indices_directory, 'ndvi')):
        os.makedirs(os.path.join(indices_directory, 'ndvi'))

    # Check which dates we already have NDVI for
    existing_files = os.listdir(os.path.join(indices_directory, 'ndvi'))
    existing_datetimes = [file[:-9] for file in existing_files]
    existing_datetimes = list(set(existing_datetimes))
    ndvi_mosaics = [mosaic for mosaic in mosaics if mosaic[:-4] not in existing_datetimes]

    if len(ndvi_mosaics) == 0:
        print('All input images already have NDVI mosaics. Moving on...')
    if len(ndvi_mosaics) == len(mosaics):
        print('Making NDVI mosaics for ' + str(len(ndvi_mosaics)) + ' images...')
    else:
        print('NDVI images already found for ' + str(len(mosaics)-len(ndvi_mosaics)) + ' input mosaics. Calculating NDVI for ' + str(len(ndvi_mosaics)) + ' dates...')

    # Loop through all mosaics and make an NDVI mosaic for each one
    for mosaic in ndvi_mosaics:
        print('Making NDVI mosaic for ' + mosaic + '...')
        ndvi = get_ndvi(os.path.join(mosaic_directory, mosaic))
        ndvi.rio.to_raster(os.path.join(indices_directory, 'ndvi', mosaic[:-4] + '_ndvi.tif'))



# NDWI: Normalized Difference Water Index
if make_ndwi:
    # Check if there is an NDWI directory; if not, make one
    if not os.path.exists(os.path.join(indices_directory, 'ndwi')):
        os.makedirs(os.path.join(indices_directory, 'ndwi'))

    # Check which dates we already have NDWI for
    existing_files = os.listdir(os.path.join(indices_directory, 'ndwi'))
    existing_datetimes = [file[:-9] for file in existing_files]
    existing_datetimes = list(set(existing_datetimes))
    ndwi_mosaics = [mosaic for mosaic in mosaics if mosaic[:-4] not in existing_datetimes]

    if len(ndwi_mosaics) == 0:
        print('All input images already have NDWI mosaics. Moving on...')
    if len(ndwi_mosaics) == len(mosaics):
        print('Making NDWI mosaics for ' + str(len(ndwi_mosaics)) + ' images...')
    else:
        print('NDWI images already found for ' + str(len(mosaics)-len(ndwi_mosaics)) + ' input mosaics. Calculating NDWI for ' + str(len(ndwi_mosaics)) + ' dates...')

    # Loop through all mosaics and make an NDWI mosaic for each one
    for mosaic in ndwi_mosaics:
        print('Making NDWI mosaic for ' + mosaic + '...')
        ndwi = get_ndwi(os.path.join(mosaic_directory, mosaic))
        ndwi.rio.to_raster(os.path.join(indices_directory, 'ndwi', mosaic[:-4] + '_ndwi.tif'))



# MSAVI2: Modified Soil Adjusted Vegetation Index 2
if make_msavi2:
    # Check if there is an MSAVI2 directory; if not, make one
    if not os.path.exists(os.path.join(indices_directory, 'msavi2')):
        os.makedirs(os.path.join(indices_directory, 'msavi2'))

    # Check which dates we already have MSAVI2 for
    existing_files = os.listdir(os.path.join(indices_directory, 'msavi2'))
    existing_datetimes = [file[:-9] for file in existing_files]
    existing_datetimes = list(set(existing_datetimes))
    msavi2_mosaics = [mosaic for mosaic in mosaics if mosaic[:-4] not in existing_datetimes]

    if len(msavi2_mosaics) == 0:
        print('All input images already have MSAVI2 mosaics. Moving on...')
    if len(msavi2_mosaics) == len(mosaics):
        print('Making MSAVI2 mosaics for ' + str(len(msavi2_mosaics)) + ' images...')
    else:
        print('MSAVI2 images already found for ' + str(len(mosaics)-len(msavi2_mosaics)) + ' input mosaics. Calculating MSAVI2 for ' + str(len(msavi2_mosaics)) + ' dates...')

    # Loop through all mosaics and make an MSAVI2 mosaic for each one
    for mosaic in msavi2_mosaics:
        print('Making MSAVI2 mosaic for ' + mosaic + '...')
        msavi2 = get_msavi2(os.path.join(mosaic_directory, mosaic))
        msavi2.rio.to_raster(os.path.join(indices_directory, 'msavi2', mosaic[:-4] + '_msavi2.tif'))



# MTVI2: Modified Triangular Vegetation Index 2
if make_mtvi2:
    # Check if there is an MTVI2 directory; if not, make one
    if not os.path.exists(os.path.join(indices_directory, 'mtvi2')):
        os.makedirs(os.path.join(indices_directory, 'mtvi2'))

    # Check which dates we already have MTVI2 for
    existing_files = os.listdir(os.path.join(indices_directory, 'mtvi2'))
    existing_datetimes = [file[:-9] for file in existing_files]
    existing_datetimes = list(set(existing_datetimes))
    mtvi2_mosaics = [mosaic for mosaic in mosaics if mosaic[:-4] not in existing_datetimes]

    if len(mtvi2_mosaics) == 0:
        print('All input images already have MTVI2 mosaics. Moving on...')
    if len(mtvi2_mosaics) == len(mosaics):
        print('Making MTVI2 mosaics for ' + str(len(mtvi2_mosaics)) + ' images...')
    else:
        print('MTVI2 images already found for ' + str(len(mosaics)-len(mtvi2_mosaics)) + ' input mosaics. Calculating MTVI2 for ' + str(len(mtvi2_mosaics)) + ' dates...')

    # Loop through all mosaics and make an MTVI2 mosaic for each one
    for mosaic in mtvi2_mosaics:
        print('Making MTVI2 mosaic for ' + mosaic + '...')
        mtvi2 = get_mtvi2(os.path.join(mosaic_directory, mosaic))
        mtvi2.rio.to_raster(os.path.join(indices_directory, 'mtvi2', mosaic[:-4] + '_mtvi2.tif'))
        


# VARI: Visible Atmospherically Resistant Index
if make_vari:
    # Check if there is an VARI directory; if not, make one
    if not os.path.exists(os.path.join(indices_directory, 'vari')):
        os.makedirs(os.path.join(indices_directory, 'vari'))

    # Check which dates we already have VARI for
    existing_files = os.listdir(os.path.join(indices_directory, 'vari'))
    existing_datetimes = [file[:-9] for file in existing_files]
    existing_datetimes = list(set(existing_datetimes))
    vari_mosaics = [mosaic for mosaic in mosaics if mosaic[:-4] not in existing_datetimes]

    if len(vari_mosaics) == 0:
        print('All input images already have VARI mosaics. Moving on...')
    if len(vari_mosaics) == len(mosaics):
        print('Making VARI mosaics for ' + str(len(vari_mosaics)) + ' images...')
    else:
        print('VARI images already found for ' + str(len(mosaics)-len(vari_mosaics)) + ' input mosaics. Calculating VARI for ' + str(len(vari_mosaics)) + ' dates...')

    # Loop through all mosaics and make an VARI mosaic for each one
    for mosaic in vari_mosaics:
        print('Making VARI mosaic for ' + mosaic + '...')
        vari = get_vari(os.path.join(mosaic_directory, mosaic))
        vari.rio.to_raster(os.path.join(indices_directory, 'vari', mosaic[:-4] + '_vari.tif'))



# TGI: Triangular Greenness Index
if make_tgi:
    # Check if there is an TGI directory; if not, make one
    if not os.path.exists(os.path.join(indices_directory, 'tgi')):
        os.makedirs(os.path.join(indices_directory, 'tgi'))

    # Check which dates we already have TGI for
    existing_files = os.listdir(os.path.join(indices_directory, 'tgi'))
    existing_datetimes = [file[:-9] for file in existing_files]
    existing_datetimes = list(set(existing_datetimes))
    tgi_mosaics = [mosaic for mosaic in mosaics if mosaic[:-4] not in existing_datetimes]

    if len(tgi_mosaics) == 0:
        print('All input images already have TGI mosaics. Moving on...')
    if len(tgi_mosaics) == len(mosaics):
        print('Making TGI mosaics for ' + str(len(tgi_mosaics)) + ' images...')
    else:
        print('TGI images already found for ' + str(len(mosaics)-len(tgi_mosaics)) + ' input mosaics. Calculating TGI for ' + str(len(tgi_mosaics)) + ' dates...')

    # Loop through all mosaics and make an TGI mosaic for each one
    for mosaic in tgi_mosaics:
        print('Making TGI mosaic for ' + mosaic + '...')
        tgi = get_tgi(os.path.join(mosaic_directory, mosaic))
        tgi.rio.to_raster(os.path.join(indices_directory, 'tgi', mosaic[:-4] + '_tgi.tif'))