import os
import geopandas as gpd

# Define the input and output directories
input_directory = "NRS_boundingbox_shapefiles"
output_directory = "NRS_boundingbox_geojsons"

# Create the output directory if it doesn't exist
if not os.path.exists(output_directory):
    os.makedirs(output_directory)

# Loop through all files in the input directory
for filename in os.listdir(input_directory):
    if filename.endswith(".shp"):  # Check if it's a shapefile
        # Construct the full path to the shapefile
        shapefile_path = os.path.join(input_directory, filename)

        # Read the shapefile into a GeoDataFrame
        gdf = gpd.read_file(shapefile_path)

        # Define the output GeoJSON file path
        output_geojson_path = os.path.join(output_directory, filename.replace(".shp", ".geojson"))

        # Save the GeoDataFrame as GeoJSON
        gdf.to_file(output_geojson_path, driver="GeoJSON")

        print(f"Converted and saved: {output_geojson_path}")
