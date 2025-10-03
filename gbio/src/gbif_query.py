import numpy as np

import requests
import os

import gbio
import gbio.src.parse.yaml as yml

from importlib.resources import files

CONFIG_PATH: str = str(files(gbio).joinpath("config.yml"))

class GBIFIO:
    def __init__(self, config_path: str=CONFIG_PATH, silent: bool=True) -> None:
        # No functionality needed, will load url from config
        self.config_data = yml.load_yaml(config_path)
        try:
            self.endpoint = self.config_data.get('api-paths').get('GBIF').get('url')
        except:
            print(f"Failed to get endpoint: {self.config_data}")

        print("Initialized GBIF IO")
        if not silent:
            print(f"   Dataset loaded: {self.config_data}")
    
    # Packaging variables for requests
    def request_by_geofence(self, 
                            coord: tuple[float, float], # (lat, lon)
                            dim: float = 1.0):
        lon_deg, lat_deg = self.km_to_deg(
            km=dim, 
            lat=coord[0])
        params = {
            'geometry': self.generate_request_polygon(
                lat=coord[0], 
                lon=coord[1], 
                dim=(lon_deg * 2, lat_deg * 2)
                ),
        }
        return self.request(
            params=params
            )
    def request(self, 
                params: dict
                ):
        try:
            res = requests.get(
                self.endpoint,
                params=params,
                )
            print(res.request.url)
        except requests.exceptions.RequestException as e:
            print(f"Failed to get request: {e}")
            return None
        
        if res.status_code != 200:
            print(f"Failed: Returned status code of {res.status_code}, with message: {res.json()}")
            return None
        
        data = res.json()
        return data

    def km_to_deg(self, km: float, lat: float):
        lat_deg = km / 111.0
        lon_deg = km / (111.320 * np.cos(np.deg2rad(lat)))
        return lon_deg, lat_deg
    def generate_request_polygon(self, lon: float, lat: float, dim: tuple[float, float]):
        lon_mp = dim[0]/2.0
        lat_mp = dim[1]/2.0

        lon_min = lon - lon_mp
        lon_max = lon + lon_mp

        lat_min = lat - lat_mp
        lat_max = lat + lat_mp

        polygon = f"POLYGON(({lon_min} {lat_min}, {lon_min} {lat_max}, {lon_max} {lat_max}, {lon_max} {lat_min}, {lon_min} {lat_min}))"
        return polygon

g = GBIFIO(silent=False)
res = g.request_by_geofence((51.530583299426304, -0.2164985443965517))