# Bounding box coordinates
xmin = 22.68
xmax = 22.82
ymin = 39.493
ymax = 39.573

selected_date = "2024-07-15" 

# Output directory and file naming
#output_directory = "./output"
output_directory = "./output"
base_name = "lake_analysis"

# Band selection for "get_data" mode: "all_bands", "rgb_only", or "rgb_nir_swir"
band_selection = "all_bands"

# SCL flags to exclude - use human-readable names like:
# "Cloud shadows", "Cloud medium probability", "Cloud high probability", "Thin cirrus", "Snow or ice", etc.
excluded_flags = ["Cloud shadows", "Cloud medium probability", "Cloud high probability"]

# Cloud cover percentage for the entire tile (0-100)
# This filters tiles based on the 'eo:cloud_cover' metadata property.
# 100 means we accept tiles with any amount of clouds.
max_cloud_tile = 100

# Days to add/subtract from selected_date to create the search window
# The search range will be [selected_date - extra_days, selected_date + extra_days]
extra_days = 15

# Maximum cloud coverage for ALLOWING a download (0-100)
# If the best image found has cloud cover > max_cloud_tolerance, it will strictly NOT be downloaded.
# Statistics will still be reported in the .txt file.
max_cloud_tolerance = 20

# Satellite platform: "sentinel-2-l2a" or "landsat-c2-l2"
# platform = "sentinel-2-l2a"
platform = "landsat-c2-l2"
