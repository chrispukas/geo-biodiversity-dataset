import gbio
import numpy as np
import geemap
import time

import ee

class SENTINELIO:
    def __init__(self):
        pass


def km_to_deg(km: float, lat: float):
        lat_deg = km / 111.0
        lon_deg = km / (111.320 * np.cos(np.deg2rad(lat)))
        return lon_deg, lat_deg

def get_rect(lon: float, lat: float, w_km: float):
    lon_mp, lat_mp = km_to_deg(km=w_km/2.0, lat=lat)

    lon_min = lon - lon_mp
    lon_max = lon + lon_mp

    lat_min = lat - lat_mp
    lat_max = lat + lat_mp

    return  ee.Geometry.Rectangle([
        lon_min, lat_min,
        lon_max, lat_max
    ])

def pull_sat_image(geom: ee.Geometry, out_path: str):
    collection = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
                  .filterBounds(geom)
                  .filterDate('2024-01-01', '2024-12-31')
                  .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
                  .median()
                  .clip(geom)
                  )
    geemap.ee_export_image(
        collection,
        filename=out_path,
        scale=10,
        region=geom,
        file_per_band=False
    )
    print(f"Downloaded to {out_path}")



def get_grid(lon_min: float, lon_max: float, lat_min: float, lat_max: float, w_km: float):
    lon_step, lat_step = km_to_deg(km=w_km, lat=(lat_min+lat_max)/2.0)
    lon_vals = np.arange(lon_min, lon_max, lon_step)
    lat_vals = np.arange(lat_min, lat_max, lat_step)

    i = 0
    for lon in lon_vals:
        for lat in lat_vals:
            r = get_rect(lon=lon, lat=lat, w_km=w_km)
            out_path = f"/Users/apple/Documents/github/geo-biodiversity-dataset/dataset/sat/tile_{i}.png"
            i+=1



ee.Authenticate()
ee.Initialize(project="geofenced-biodiversity-project")

geom = get_rect(lon=-122.55, lat=37.65, w_km=2.0) 

collection = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
                  .filterBounds(geom)
                  .filterDate('2024-01-01', '2024-12-31')
                  .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
                  .median()
                  .clip(geom)
                  )

task = ee.batch.Export.image.toDrive(
    image=collection,
    description='tile_1km',
    folder='GEE_tiles',
    fileNamePrefix='tile_1km',
    scale=10,
    region=geom,
    crs='EPSG:4326'
)
task.start()

while task.status()['state'] in ['READY', 'RUNNING']:
    print(task.status())
    time.sleep(10)  # wait 10 seconds before checking again

#pull_sat_image(geom=get_rect(lon=-122.55, lat=37.65, w_km=1.0), 
#               out_path="/Users/apple/Documents/github/geo-biodiversity-dataset/dataset/sat/test.tif")