import numpy as np

import requests
import os

import gbio
import gbio.src.parse.yaml as yml
import gbio.src.cache as cache

from importlib.resources import files

CONFIG_PATH: str = str(files(gbio).joinpath("config.yml"))

class GBIFIO:
    def __init__(self, config_path: str=CONFIG_PATH, silent: bool=True) -> None:
        # No functionality needed, will load url from config
        self.config_data = yml.load_yaml(config_path)
        try:
            self.endpoint = self.config_data.get('api-paths').get('GBIF_SEARCH').get('url')
            self.endpoint_species = self.config_data.get('api-paths').get('GBIF_SPECIES').get('url')
        except:
            print(f"Failed to get endpoint: {self.config_data}")

        print("Initialized GBIF IO")
        if not silent:
            print(f"   Dataset loaded: {self.config_data}")

        self.species_cache = {}
        self.cache = cache.Cache(pickle_name="species_cache")
        if self.cache.is_pickle():
            self.species_cache = self.cache.load_pickle()

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
            'limit': 0,
            "hasCoordinate": True,
            'facet': 'speciesKey',
            'facetLimit': 1000,
            'taxonKey': 1, # Animalia
        }
        return self.request(
            params=params
            )
    
    def bucket_redlist(self, 
                        data: dict
                        ):
        # Bucket the data by IUCN Red List status
        buckets = {
            'EX': [],
            'EW': [],
            'CR': [],
            'EN': [],
            'VU': [],
            'NT': [],
            'LC': [],
            'DD': [],
            'NE': [],
        }
        for record in data.get('results', []):
            status = record.get('iucnRedListCategory', 'NE')
            if status in buckets:
                buckets[status].append(record)
            else:
                buckets['NE'].append(record)
        return buckets

    def process_output(self, data: dict):
        if data is None:
            return None
        s_entries = data.get('facets', [])[0].get('counts', [])

        redlist_buckets = {
            'redlist_EX': 0,
            'redlist_EW': 0,
            'redlist_CR': 0,
            'redlist_EN': 0,
            'redlist_VU': 0,
            'redlist_NT': 0,
            'redlist_LC': 0,
            'redlist_DD': 0,
            'redlist_NE': 0,
        }

        species = []
        for entry in s_entries:
            species_key = int(entry.get('name'))
            species_info = self.get_species_name(species_key)
            redlist_buckets[f"redlist_{species_info.get('redlist', {}).get('code')}"] += 1
            species.append(species_info)

        final_entry = {
            'species_richness': len(s_entries),
        }
        final_entry.update(redlist_buckets)

        
        return final_entry
    
    def request(self, 
                params: dict,
                endpoint: str = None,
                ):
        try:
            res = requests.get(
                endpoint or self.endpoint,
                params=params,
                )
        except requests.exceptions.RequestException as e:
            print(f"Failed to get request: {e}")
            return None
        
        if res.status_code != 200:
            print(f"Failed: Returned status code of {res.status_code}, with message: {res}")
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
    

    def get_species_name(self, species_key: int):
        if species_key in self.species_cache:
            return self.species_cache[species_key]
        
        params = {
            'speciesKey': species_key
        }
        data = self.request(params=params,
                            endpoint=f"{self.endpoint_species}/{species_key}"
                            )
        redlist = self.request(params=params,
                            endpoint=f"{self.endpoint_species}/{species_key}/iucnRedListCategory"
                            )
        if data and redlist:
            data['redlist'] = redlist # Add redlist info if available
            self.species_cache[species_key] = data
            print("Pulling from GBIF API with species key:", species_key)
            return data
        else:
            return None