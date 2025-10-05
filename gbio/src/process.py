import os
import cv2

import pandas as pd
import time
import numpy as np

from tqdm import tqdm

import gbio.src.gbif_query as gbq

sharpness_kernel = np.array([
    [0, -1, 0],
    [-1, 5, -1],
    [0, -1, 0],
])

GAMMA = 1.5


g = gbq.GBIFIO(silent=False)

def apply_filters(img):
    img_cropped = img[0:150, 0:225]
    sharpened = cv2.filter2D(img_cropped, -2, sharpness_kernel)
    gamma_corrected = np.uint8(255 * (sharpened / 255) ** (1/GAMMA))
    return gamma_corrected

def gen_entry(img_name: str,
              variation: int,
              city: str,
              ) -> dict:
    id, name, lon, lat = img_name.split('_')
    lat = lat.split('.jpg')[0]

    return {
        "full_name": str(img_name),
        "city": str(city),
        "variation": int(variation),
        "longitude": float(lon),
        "latitude": float(lat),
    }




def process_img(img_path: str, 
                out_path: str,
                city: str) -> list[dict]:
    img = cv2.imread(img_path)
    img = apply_filters(img=img)

    rotated_180 = cv2.rotate(img, cv2.ROTATE_180)
    flip_1 = cv2.flip(img, 1) # Horizontal Flip
    flip_2 = cv2.flip(img, 0) # Vertical Flip
    rots = [img, rotated_180, flip_1, flip_2]

    f_name = os.path.basename(out_path).replace(".tif", '.jpg')
    d_name = os.path.dirname(out_path)

    entries = []

    global g

    name, lon, lat = f_name.split('_')
    lat = lat.split('.jpg')[0]

    try:
        gbif_data = g.request_by_geofence(coord=(float(lon), float(lat)))
        gbif_data = g.process_output(gbif_data)
    except Exception as e:
        print(f"Error querying GBIF for image {f_name} at coords {(lon, lat)}: {e}")
        gbif_data = None

    if gbif_data is None:
        print(f"No GBIF data found for image: {f_name} at coords: {(lon, lat)}")
        return []

    for i, r in enumerate(rots):
        iter_name = f"{i}_{f_name}"
        cv2.imwrite(os.path.join(d_name, iter_name), r)
        e = gen_entry(
            img_name=iter_name, 
            variation=i,
            city=city,
        )
        if gbif_data is not None:
            e.update(gbif_data)
        entries.append(e)
    return entries
    


def create_df(output_path: str, 
              data: list[dict]) -> None:
    df = pd.DataFrame(data=data)
    df.index.name = "id"
    df.to_csv(output_path)

    print(f"Sucessfully created df with cols: {df.columns}, and size: {df.shape}.")

def process_sats(input_path_raw: str, 
                 output_path: str, 
                 csv_path: str,
                 override: bool = False,
                 skip: list[str] = None) -> None:
    if skip is None:
        skip = []
    
    dirs: str = os.listdir(input_path_raw)
    for dir in dirs:
        dir_path: str = os.path.join(input_path_raw, dir)
        if dir_path.endswith('.DS_Store'):
            continue
        city: str = os.path.basename(dir_path)

        if city in skip:
            print(f"Skipping city: {city}")
            continue
        print(f"Processing city: {city}")

        imgs: str = os.listdir(dir_path)

        save_dir: str = os.path.join(output_path, city)
        os.makedirs(save_dir, exist_ok=True)
        entries = []
        
        for img in tqdm(imgs):
            img_path: str = os.path.join(dir_path, img)
            out_path: str = os.path.join(save_dir, img)

            if not override and os.path.exists(out_path):
                print(f"Image already processed: {img}")
                continue


            e_new: list[dict] = process_img(img_path=img_path, 
                        out_path=out_path,
                        city=city)
            entries.extend(e_new)

            g.cache.save_pickle(g.species_cache, pickle_name="species_cache")
        
        df_path: str = os.path.join(csv_path, f"{city}.csv")
        create_df(df_path, entries)




def combine_csvs(input_path: str, 
                 output_file: str) -> None:
    files = os.listdir(input_path)
    all_dfs = []
    for f in files:
        if f.endswith('.csv'):
            df = pd.read_csv(os.path.join(input_path, f), index_col=False).drop(labels="id", axis=1)
            all_dfs.append(df)
    combined_df = pd.concat(all_dfs, ignore_index=True)
    combined_df.index.name = "id"
    combined_df.to_csv(output_file)
    print(f"Combined CSV saved to {output_file} with shape {combined_df.shape}.")
