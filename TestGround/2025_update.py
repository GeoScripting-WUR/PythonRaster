
# From : https://geog-312.gishub.org/book/geospatial/rasterio.html#reading-raster-data
import rasterio
import rasterio.plot

import geopandas as gpd
import numpy as np
import matplotlib.pyplot as plt


raster_path = (
    "https://github.com/opengeos/datasets/releases/download/raster/dem_90m.tif"
)
src = rasterio.open(raster_path)

print(src.name)

# rasterio.plot.show((src, 1))
rasterio.plot.show(src)

fig, ax = plt.subplots(figsize=(8, 8))
rasterio.plot.show(src, cmap="terrain", ax=ax, title="Digital Elevation Model (DEM)")
plt.show()