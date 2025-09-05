import json
from pystac import Catalog, get_stac_version
import shapely.geometry as geom
from shapely.geometry import Polygon


root_catalog = Catalog.from_file('https://stac.dataspace.copernicus.eu/v1/')
collections = root_catalog.map_assets(1).get_all_collections()

# eg: Wageningen polygon ~ (5.666, 51.966)
wageningen_poly = geom.Polygon([
    (5.65, 51.95),
    (5.68, 51.95),
    (5.68, 51.98),
    (5.65, 51.98),
    (5.65, 51.95)
])

wageningen_collection = []

for icol in collections:
    bbox = icol.extent.spatial.bboxes[0]

    collection_extent = Polygon([
        (bbox[0], bbox[1]),  # lower-left
        (bbox[2], bbox[1]),  # lower-right
        (bbox[2], bbox[3]),  # upper-right
        (bbox[0], bbox[3]),  # upper-left
        (bbox[0], bbox[1])   # close polygon
    ])

    if collection_extent.contains(wageningen_poly):
        wageningen_collection.append(icol)

print(f"Number of collections covering Wageningen: {len(wageningen_collection)}")