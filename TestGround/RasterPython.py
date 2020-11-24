#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Geoscripting 2020
Lesson 11 - Python Raster
v20201124
CHappyhill
"""
import os
if not os.path.exists('data'): os.makedirs('data')
if not os.path.exists('output'): os.makedirs('output')

import matplotlib.pyplot as plt

import tarfile
from urllib.request import urlretrieve

directory = './data/'
tarfilename = directory + "landsat.tar.gz"

if not os.path.isfile(tarfilename):
    url = 'https://www.dropbox.com/s/zb7nrla6fqi1mq4/LC81980242014260-SC20150123044700.tar.gz?dl=1'
    urlretrieve(url, tarfilename)
    tar = tarfile.open(tarfilename)
    tar.extractall(path=directory)
    tar.close()
    
import numpy as np
import rasterio
from rasterio.plot import show

greenband = rasterio.open(directory + "LC81980242014260LGN00_sr_band4.tif")
mirband = rasterio.open(directory + "LC81980242014260LGN00_sr_band6.tif")

green = greenband.read(1).astype(float)
mir = mirband.read(1).astype(float)

np.seterr(divide='ignore', invalid='ignore')  # Allow division by zero
mndwi = np.empty(greenband.shape, dtype=rasterio.float32)  # Create empty matrix
check = np.logical_or(mir > 0.0, green > 0.0)  # Create check raster with True/False values
mndwi = np.where(check, (green - mir) / (green + mir), -999)  # Calculate MNDWI

water = np.where(mndwi > 0, 1, 0) # Set values above 0 as water and otherwise leave it at 0
show(water, cmap='Blues')

from owslib.wcs import WebCoverageService
wcs = WebCoverageService('http://geodata.nationaalgeoregister.nl/ahn2/wcs?service=WCS', version='1.0.0')
print(list(wcs.contents))

print([op.name for op in wcs.operations])

cvg = wcs.contents['ahn2_05m_ruw']
print(cvg.boundingBoxWGS84)
print(cvg.supportedCRS)
print(cvg.supportedFormats)

x, y = 174100, 444100
bbox = (x-500, y-500, x+500, y+500)
response = wcs.getCoverage(identifier='ahn2_05m_ruw', bbox=bbox, format='GEOTIFF_FLOAT32',
                           crs='urn:ogc:def:crs:EPSG::28992', resx=0.5, resy=0.5)
with open('./data/AHN2_05m_DSM.tif', 'wb') as file:
    file.write(response.read())

response = wcs.getCoverage(identifier='ahn2_05m_int', bbox=bbox, format='GEOTIFF_FLOAT32',
                           crs='urn:ogc:def:crs:EPSG::28992', resx=0.5, resy=0.5)
with open('./data/AHN2_05m_DTM.tif', 'wb') as file:
    file.write(response.read())

import rasterio
DSM = rasterio.open("./data/AHN2_05m_DSM.tif", driver="GTiff")
DTM = rasterio.open("./data/AHN2_05m_DTM.tif", driver="GTiff")
print(DSM.meta)
print(DTM.meta)
show(DSM, title='Digital Surface Model', cmap='gist_ncar')

print(type(DSM))
print(type(DSM.read(1)))

print(DSM.read(1))

CHM = DSM.read() - DTM.read()
print(type(CHM))

kwargs = DSM.meta # Copy metadata of rasterio.io.DatasetReader
with rasterio.open('./data/AHN2_05m_CHM.tif', 'w', **kwargs) as file:
    file.write(CHM.astype(rasterio.float32))

import geopandas as gpd
from requests import Request
# extract only buildings on and around WUR campus
url = 'https://geodata.nationaalgeoregister.nl/bag/wfs/v1_1'
layer = 'bag:pand' # see wfs.contents
bb = ','.join(map(str, bbox)) # string of bbox needed for the request url
# Specify the parameters for fetching the data
params = dict(service='WFS', version="1.1.0", request='GetFeature',
      typeName=layer, outputFormat='json',
      srsname='urn:ogc:def:crs:EPSG::28992', bbox=bb)
# Parse the URL with parameters
q = Request('GET', url, params=params).prepare().url
# Read data from URL
BuildingsGDF = gpd.read_file(q)

import rasterstats as rs
CHMbuildings = rs.zonal_stats(BuildingsGDF, "./data/AHN2_05m_CHM.tif", prefix='CHM_', geojson_out=True)
BuildingsGDF = gpd.GeoDataFrame.from_features(CHMbuildings)
# check the added columns with a prefix 'CHM_'
print(BuildingsGDF['CHM_mean'])

import matplotlib.pyplot as plt
fig, ax = plt.subplots(1, figsize=(10, 10)) # Create one plot with figure size 10 by 10
ax.set_title('Buildings on the WUR campus and their heights above ground')
BuildingsGDF.plot(ax=ax, column='CHM_mean', k=6, 
                  cmap=plt.cm.viridis, linewidth=1, edgecolor='black', legend=True)
ax.set_facecolor("lightgray") # Set background to grey
plt.axis('equal') # Set equal axis 
plt.show() # Visualize figure 
#plt.savefig('./outputimages/buildingsGDF.png')

import affine
kwargs = {'driver': 'GTiff',
          'dtype': 'float32',
          'nodata': None,
          'width': 2000,
          'height': 2000,
          'count': 1,
          'crs': rasterio.crs.CRS({'init': 'epsg:28992'}),
          'transform': affine.Affine(0.5, 0.0, 173600.0, 0.0, -0.5, 444600.0)}
# kwargs = DSM.meta # Metadata can be copied from existing file if needed
with rasterio.open('./data/AHN2_05m_CHM.tif', 'w', **kwargs) as file:
    file.write(CHM.astype(rasterio.float32))

CHM = rasterio.open("./data/AHN2_05m_CHM.tif")
print(CHM.meta)

import matplotlib.pyplot as plt
fig, ax = plt.subplots(figsize=(10,10))
dsmplot = ax.imshow(DSM.read(1), cmap='Oranges', extent=bbox)
ax.set_title("Digital Surface Model - WUR Campus", fontsize=14)
cbar = fig.colorbar(dsmplot, fraction=0.035, pad=0.01)
cbar.ax.get_yaxis().labelpad = 15
cbar.ax.set_ylabel('Height (m)', rotation=270)
ax.set_axis_off()
plt.show()
#plt.savefig('./outputimages/DSMgood.png')

fig, ax = plt.subplots(figsize=(10,10))
dtmplot = ax.imshow(DTM.read(1), cmap='Oranges', extent=bbox)
ax.set_title("Digital Terrain Model - WUR Campus", fontsize=14)
cbar = fig.colorbar(dtmplot, fraction=0.035, pad=0.01, extend='both')
cbar.ax.get_yaxis().labelpad = 15
cbar.ax.set_ylabel('Height (m)', rotation=270)
ax.set_axis_off()
plt.show()

from rasterio.plot import show
fig, (axdsm, axdtm, axchm) = plt.subplots(1, 3, figsize=(21, 7))
show(DSM, ax=axdsm, title='DSM')
show(DTM, ax=axdtm, title='DTM')
show(CHM, ax=axchm, title='CHM')
plt.show()
#plt.savefig('./outputimages/DSMDTMCHMImage.png')

from rasterio.plot import show_hist
fig, (axdsm, axdtm, axchm) = plt.subplots(1, 3, figsize=(21, 7))
show_hist(DSM, ax=axdsm, bins=100, lw=0.0, stacked=False, alpha=0.3, title="Histogram DSM")
show_hist(DTM, ax=axdtm, bins=100, lw=0.0, stacked=False, alpha=0.3, title="Histogram DTM")
show_hist(CHM, ax=axchm, bins=100, lw=0.0, stacked=False, alpha=0.3, title="Histogram CHM")
axdsm.legend(['DSM'])
axdtm.legend(['DTM'])
axchm.legend(['CHM'])
plt.show()

plt.savefig('./images/DSMDTMCHMHistogram2.png')
















