import cv2
import os
import numpy as np

import pandas as pd

from tqdm import tqdm


def create_landcover_map(img_path: str, output_path: str) -> float:
    # Read image
    img = cv2.imread(img_path)
    if img is None:
        raise ValueError(f"Image not found at {img_path}")
    green_channel = img[:, :, 1]
    vegetation_mask = green_channel > 100

    cv2.imwrite(output_path, vegetation_mask.astype(np.uint8) * 255)

    lc_percent = vegetation_mask.sum() / vegetation_mask.size

    return lc_percent

def process_sats(input_path_raw: str, 
                 output_path: str, 
                 csv_path: str,
                 override: bool = False,
                 skip: list[str] = None) -> None:
    if skip is None:
        skip = []
    
    cities = os.listdir(input_path_raw)
    for city_folder in cities:
        input_city_path = os.path.join(input_path_raw, city_folder)
        city = os.path.basename(input_city_path)
        if city_folder.endswith('.DS_Store') or city in skip:
            continue
        print(f"Processing city: {city}")

        csv_file = os.path.join(csv_path, f"{city}.csv")
        df = pd.read_csv(csv_file)
        lc_percent_col = []
        lc_obj_col = []

        output_city_dir = os.path.join(output_path, city)
        os.makedirs(output_city_dir, exist_ok=True)

        for row in tqdm(df.itertuples()):
            img_name = row.full_name
            input_img_path = os.path.join(input_city_path, img_name)
            output_name = f"{img_name.replace('.jpg', '')}_landcover.jpg"
            output_img_path = os.path.join(output_city_dir, output_name)

            lc_percent = create_landcover_map(input_img_path, output_img_path)
            lc_percent_col.append(lc_percent)
            lc_obj_col.append(output_name)

        df['landcover_percent'] = lc_percent_col
        df['landcover_object'] = lc_obj_col
        df.to_csv(csv_file, index=False)
