import os
import geopandas as gpd

# Directory containing the input shapefiles
input_directory = "NRS_Boundary/separate"

# Directory where processed shapefiles will be saved
output_directory = "output_dir"

# Create the output directory if it doesn't exist
os.makedirs(output_directory, exist_ok=True)

# EPSG code for Albers Equal Area Conic projection for California
target_epsg = 'EPSG:3310'

# EPSG code for reprojecting back to EPSG 4326 (WGS 84)
reproject_epsg = 'EPSG:4326'

# Get a list of all shapefiles in the "input_dir"
shapefiles = [file for file in os.listdir(input_directory) if file.endswith(".shp")]

# Loop over each shapefile and perform the required operations
for shapefile in shapefiles:
    # Construct the full path to the input shapefile
    input_shapefile_path = os.path.join(input_directory, shapefile)

    # Read the input shapefile into a GeoDataFrame
    gdf = gpd.read_file(input_shapefile_path)

    # Reproject the GeoDataFrame to EPSG 3310 (Albers Equal Area Conic)
    gdf = gdf.to_crs(target_epsg)

    # Calculate the geodesic area in square kilometers and add it as a new attribute
    gdf["Area_Sq_Km"] = gdf.geometry.area / 10**6

    # Keep only the "Area_Sq_Km" attribute and the geometry column
    gdf = gdf[["geometry", "Area_Sq_Km"]]

    # Reproject the GeoDataFrame to EPSG 4326 (WGS 84)
    gdf = gdf.to_crs(reproject_epsg)

    # Define the output path for the processed shapefile in the output directory
    output_shapefile = os.path.join(output_directory, shapefile)

    # Save the processed GeoDataFrame as a new shapefile
    gdf.to_file(output_shapefile)

    print(f"Processed {shapefile} and saved as {output_shapefile}")

print("All shapefiles in the 'input_dir' have been processed and saved in the 'output_dir'.")
