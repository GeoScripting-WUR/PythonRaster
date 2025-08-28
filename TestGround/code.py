import rasterio
from owslib.wcs import WebCoverageService
import numpy as np
from rasterio.fill import fillnodata
import matplotlib.pyplot as plt

# Access the WCS by proving the url and optional arguments
wcs = WebCoverageService('https://service.pdok.nl/rws/ahn/wcs/v1_0?SERVICE=WCS&request=GetCapabilities', version='1.0.0')

cvg = wcs.contents['dsm_05m']

# Define a bounding box in the available crs (see before) by picking a point and drawing a 1x1 km box around it
x, y = 174100, 444100
bbox = (x - 500, y - 500, x + 500, y + 500)

# Request the DSM data from the WCS
response = wcs.getCoverage(identifier='dsm_05m', bbox=bbox, format='GEOTIFF',
                           crs='urn:ogc:def:crs:EPSG::28992', resx=0.5, resy=0.5)

# Write the data to a local file in the 'data' directory
with open('data/AHN3_05m_DSM.tif', 'wb') as file:
    file.write(response.read())

# Do the same for the DTM
response = wcs.getCoverage(identifier='dtm_05m', bbox=bbox, format='GEOTIFF',
                           crs='urn:ogc:def:crs:EPSG::28992', resx=0.5, resy=0.5)

with open('data/AHN3_05m_DTM.tif', 'wb') as file:
    file.write(response.read())


# Open the two rasters 
dsm = rasterio.open("data/AHN3_05m_DSM.tif", driver="GTiff")
dtm = rasterio.open("data/AHN3_05m_DTM.tif", driver="GTiff")


# Access the data from the two rasters
dsm_data = dsm.read()
dtm_data = dtm.read()

# Set our nodata to np.nan (this is important for later)
dsm_data[dsm_data == dsm.nodata] = np.nan
dtm_data[dtm_data == dtm.nodata] = np.nan

dtm_mask = dtm_data.copy()
dtm_mask[~np.isnan(dtm_data)] = 1
dtm_mask[np.isnan(dtm_data)] = 0

# Fill missing values
dtm_data = fillnodata(dtm_data, mask=dtm_mask)

# Subtract the NumPy arrays 
chm = dsm_data - dtm_data

# Copy metadata of one of the rasters (does not matter which one)
kwargs = dsm.meta 

# Save the chm as a raster
with rasterio.open('data/AHN3_05m_CHM.tif', 'w', **kwargs) as file:
    file.write(chm.astype(rasterio.float32))

import geopandas as gpd
import json
from owslib.wfs import WebFeatureService

# Get the WFS of the BAG
wfsUrl = 'https://service.pdok.nl/lv/bag/wfs/v2_0'
wfs = WebFeatureService(url=wfsUrl, version='2.0.0')
layer = list(wfs.contents)[0]

# Get the features for the study area
# notice that we now get them as json, in contrast to before
response = wfs.getfeature(typename=layer, bbox=bbox, outputFormat='json')
data = json.loads(response.read())

# Create GeoDataFrame, without saving first
buildings_gdf = gpd.GeoDataFrame.from_features(data['features'])

# Set crs to RD New
buildings_gdf.crs = 28992

import rasterstats as rs

# Apply the zonal statistics function with gdf and tif as input
chm_buildings = rs.zonal_stats(buildings_gdf, "data/AHN3_05m_CHM.tif", prefix='CHM_', geojson_out=True)

# Convert GeoJSON to GeoDataFrame
buildings_gdf = gpd.GeoDataFrame.from_features(chm_buildings)

# Check the added attributes with a prefix 'CHM_'
print(buildings_gdf['CHM_mean'])

# Create one plot with figure size 10 by 10
fig, ax = plt.subplots(1, figsize=(10, 10))

# Customize figure with title, legend, and facecolour
ax.set_title('Heights above ground (m) of buildings on the WUR campus')
buildings_gdf.plot(ax=ax, column='CHM_mean', k=6,
                   cmap=plt.cm.viridis, linewidth=1, edgecolor='black', legend=True)
ax.set_facecolor("lightgray")

# Make sure to get an equal scale in the x and y direction
plt.axis('equal')


from rasterio.plot import show_hist

import numpy as np

# Stack the three arrays along a new axis to create a 3-band raster
# Ensure all arrays have the same shape and are 2D
three_band_array = np.stack([dsm_data, dtm_data, chm], axis=0).squeeze()

# Copy metadata and update for 3 bands
three_band_meta = dsm.meta.copy()
three_band_meta.update(count=3)

# Write the 3-band raster to file
with rasterio.open('data/AHN3_05m_3band.tif', 'w', **three_band_meta) as dst:
  dst.write(three_band_array.astype(rasterio.float32))

with rasterio.open('data/AHN3_05m_3band.tif') as raster:
  show_hist(raster, bins=50, lw=0.0, stacked=False, alpha=0.3, 
            histtype='stepfilled', title="Histogram", label = ['dsm', 'dtm', 'chm'])
