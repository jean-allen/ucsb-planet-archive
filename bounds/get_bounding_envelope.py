import os
import geopandas as gpd
from shapely.geometry import Polygon
from shapely.geometry import box


input_directory = "NRS_shapefiles"
output_directory = "NRS_boundingbox_shapefiles"
os.makedirs(output_directory, exist_ok=True)

shapefiles = [file for file in os.listdir(input_directory) if file.endswith(".shp")]

# Calculates a bounding envelope for a geodataframe and returns that box as a new geodataframe
def create_bounding_box(gdf):
    bbox = gdf.geometry.total_bounds
    bounding_box_polygon = box(bbox[0], bbox[1], bbox[2], bbox[3])
    bbox_gdf = gpd.GeoDataFrame({'geometry': [bounding_box_polygon]}, crs=gdf.crs)
    return bbox_gdf

# Reprojects gdf to Albers equal area, calculates area, adds it as an attribute, then returns gdf in its original projection
def calculate_area(gdf):
    original_epsg = gdf.crs.to_epsg()
    gdf = gdf.to_crs('EPSG:3310')
    gdf["Area_Sq_Km"] = gdf.geometry.area / 10**6
    gdf = gdf.to_crs('EPSG:' + str(original_epsg))
    return gdf

for shapefile in shapefiles:
    gdf = gpd.read_file(os.path.join(input_directory,shapefile))
    bb = create_bounding_box(gdf)
    bb = calculate_area(bb)
    output_shapefile = os.path.join(output_directory, shapefile[:-4] + '_bb.shp')
    bb.to_file(output_shapefile)
