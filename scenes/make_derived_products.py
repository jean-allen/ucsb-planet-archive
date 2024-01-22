# create desired




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