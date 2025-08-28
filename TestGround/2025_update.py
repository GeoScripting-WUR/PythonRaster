
# # From : https://geog-312.gishub.org/book/geospatial/rasterio.html#reading-raster-data
# import rasterio
# import rasterio.plot

# import geopandas as gpd
# import numpy as np
# import matplotlib.pyplot as plt


# raster_path = (
#     "https://github.com/opengeos/datasets/releases/download/raster/dem_90m.tif"
# )
# src = rasterio.open(raster_path)

# print(src.name)

# # rasterio.plot.show((src, 1))
# rasterio.plot.show(src)

# fig, ax = plt.subplots(figsize=(8, 8))
# rasterio.plot.show(src, cmap="terrain", ax=ax, title="Digital Elevation Model (DEM)")
# plt.show()

from pystac_client import Client
from odc.stac import load
import odc.geo

# use publically available stac link such as
client = Client.open("https://earth-search.aws.element84.com/v1") 

# ID of the collection
collection = "sentinel-2-l2a"

# Geometry of AOI
geometry = {
    "coordinates": [
        [
            [74.66218437999487, 19.46556170905807],
            [74.6629598736763, 19.466339343697722],
            [74.6640371158719, 19.4667885366414],
            [74.66395296156406, 19.46614872872264],
            [74.66376889497042, 19.466150941501425],
            [74.66369077563286, 19.46577508478787],
            [74.6635865047574, 19.465278788212864],
            [74.66282073408365, 19.46540270444271],
            [74.66218437999487, 19.46556170905807],
        ]
    ],
    "type": "Polygon",
}

# Complete month
date_YYMM = "2023-01"
# run pystac client search to see available dataset
search = client.search(
    collections=[collection], intersects=geometry, datetime=date_YYMM
) 
# spit out data as GeoJSON dictionary
print(search.item_collection_as_dict())
# loop through each item
for item in search.items_as_dicts():
    print(item)