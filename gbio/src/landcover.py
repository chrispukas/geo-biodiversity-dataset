import cv2
import os
import numpy as np

import pandas as pd

from tqdm import tqdm


def create_landcover_map(img_path: str, output_path: str) -> str:
    img = cv2.imread(img_path)
    # Dummy implementation: Just return a blank map
    landcover_map = np.zeros_like(img) # (w, h, rgb)
    landcover_map = landcover_map[:, :, 1]

    cv2.imwrite(output_path, landcover_map)

    lc_percent = 0.0

    return lc_percent

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
        city: str = os.path.basename(dir_path)
        if dir_path.endswith('.DS_Store') or city in skip:
            continue
        print(f"Processing city: {city}")

        csv_file = os.path.join(csv_path, f"{city}.csv")
        df = pd.read_csv(csv_file)
        lc_percent_col = []
        lc_obj_col = []
        
        for row in tqdm(df.itertuples()):
            print(row)
            img_name: str = row.full_name
            output_name = f"{img_name.replace('.jpg', '')}_landcover.jpg"

            img_path: str = os.path.join(dir_path, img_name)
            out_path: str = os.path.join(output_path, city, output_name)
            lc_percent = create_landcover_map(img_path, out_path)

            lc_percent_col.append(lc_percent)
            lc_obj_col.append(output_name)

        df['landcover_percent'] = lc_percent_col
        df['landcover_object'] = lc_obj_col
        df.to_csv(csv_file, index=False)
