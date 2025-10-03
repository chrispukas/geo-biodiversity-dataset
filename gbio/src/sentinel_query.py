import ee
import time
import numpy as np

# ------------------------------
# Helper functions
# ------------------------------

def km_to_deg(km: float, lat: float):
    """Convert km to degrees latitude and longitude at a given latitude."""
    lat_deg = km / 111.0
    lon_deg = km / (111.320 * np.cos(np.deg2rad(lat)))
    return lon_deg, lat_deg

def get_bbox(center_lon: float, center_lat: float, width_km: float):
    """Return an ee.Geometry.Rectangle bounding box around a center point."""
    lon_offset, lat_offset = km_to_deg(km=width_km/2.0, lat=center_lat)
    lon_min = center_lon - lon_offset
    lon_max = center_lon + lon_offset
    lat_min = center_lat - lat_offset
    lat_max = center_lat + lat_offset
    return ee.Geometry.Rectangle([lon_min, lat_min, lon_max, lat_max])

def export_tile(center_lon: float, center_lat: float, width_km: float, 
                folder: str, prefix: str, scale: int = 10):
    """Export a single Sentinel-2 median image tile as GeoTIFF to Google Drive."""
    geom = get_bbox(center_lon, center_lat, width_km)
    
    collection = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
                  .filterBounds(geom)
                  .filterDate('2024-01-01', '2024-12-31')
                  .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
                  .median()
                  .clip(geom))
    
    task = ee.batch.Export.image.toDrive(
        image=collection,
        description=f'{prefix}_{center_lat}_{center_lon}',
        folder=folder,
        fileNamePrefix=f'{prefix}_{center_lat}_{center_lon}',
        scale=scale,
        region=geom,
        crs='EPSG:4326'
    )
    task.start()
    return task

# Create grid of centers
def create_grid(lon_center, lat_center, w_km, n_tiles):
    """n_tiles: number of tiles per side (odd number recommended)"""
    lon_step, lat_step = km_to_deg(w_km, lat_center)
    half = n_tiles // 2
    lon_vals = [lon_center + i * lon_step for i in range(-half, half + 1)]
    lat_vals = [lat_center + j * lat_step for j in range(-half, half + 1)]
    return [(lon, lat) for lon in lon_vals for lat in lat_vals]

def monitor_tasks(tasks, wait_sec=10):
    """Monitor a list of Earth Engine export tasks."""
    unfinished = tasks.copy()
    while unfinished:
        for t in unfinished[:]:
            status = t.status()
            print(status)
            if status['state'] in ['COMPLETED', 'FAILED', 'CANCELLED']:
                unfinished.remove(t)
        time.sleep(wait_sec)

# ------------------------------
# Example usage
# ------------------------------

ee.Authenticate()
ee.Initialize(project="geofenced-biodiversity-project")

# List of center coordinates (lon, lat)
centers = [
    (51.50594342127512, -0.12428852168536396),
]

w_km = 1.0        # tile size
tiles_per_side = 9

tasks = []
for lon_center, lat_center in centers:
    grid = create_grid(lon_center, lat_center, w_km, tiles_per_side)
    for lon, lat in grid:
        task = export_tile(lon, lat, w_km, folder='GEE_London', prefix='tile')
        tasks.append(task)

monitor_tasks(tasks)
