import os
import cv2

import pandas as pd
import time
import numpy as np

sharpness_kernel = np.array([
    [0, -1, 0],
    [-1, 5, -1],
    [0, -1, 0],
])

GAMMA = 1.5

def apply_filters(img):
    img_cropped = img[0:150, 0:225]
    sharpened = cv2.filter2D(img_cropped, -2, sharpness_kernel)
    gamma_corrected = np.uint8(255 * (sharpened / 255) ** (1/GAMMA))
    return gamma_corrected

def gen_entry(img_name: str,
              variation: int,
              city: str,
              ) -> dict:
    name, lon, lat = img_name.split('_')
    lat = lat.split('.')[0]

    return {
        "city": str(city),
        "variation": int(variation),
        "longitude": float(lon),
        "latitude": float(lat),
        "full_name": str(img_name),
    }




def process_img(img_path: str, 
                out_path: str,
                city: str) -> list[dict]:
    img = cv2.imread(img_path)
    if img.shape != (152, 247, 3):
        print(f"Mismatch in image shape: {img.shape}")
    img = apply_filters(img=img)

    rotated_180 = cv2.rotate(img, cv2.ROTATE_180)
    flip_1 = cv2.flip(img, 1) # Horizontal Flip
    flip_2 = cv2.flip(img, 0) # Vertical Flip
    rots = [img, rotated_180, flip_1, flip_2]

    f_name = os.path.basename(out_path).replace(".tif", '.jpg')
    d_name = os.path.dirname(out_path)

    entries = []

    for i, r in enumerate(rots):
        cv2.imwrite(os.path.join(d_name, f"{i}_{f_name}"), r)
        entries.append(gen_entry(
            img_name=f_name, 
            variation=i,
            city=city,
        ))
    return entries
    


def create_df(output_path: str, 
              data: list[dict]) -> None:
    df = pd.DataFrame(data=data)
    df.to_csv(output_path)

    print(f"Sucessfully created df with cols: {df.columns}, and size: {df.shape}.")

def process_sats(input_path_raw: str, 
                 output_path: str, 
                 csv_path: str) -> None:
    dirs: str = os.listdir(input_path_raw)
    for dir in dirs:
        dir_path: str = os.path.join(input_path_raw, dir)
        city: str = os.path.basename(dir_path)
        imgs: str = os.listdir(dir_path)

        save_dir: str = os.path.join(output_path, city)
        os.makedirs(save_dir, exist_ok=True)
        entries = []
        
        for img in imgs:
            img_path: str = os.path.join(dir_path, img)
            out_path: str = os.path.join(save_dir, img)
            e_new: list[dict] = process_img(img_path=img_path, 
                        out_path=out_path,
                        city=city)
            entries.extend(e_new)
            print(f"Processed image: {img}")
        


        




input_path_raw = "/Users/apple/Documents/github/geo-biodiversity-dataset/dataset/sat/raw"
output_path = "/Users/apple/Documents/github/geo-biodiversity-dataset/dataset/sat/processed"

csv_path = "/Users/apple/Documents/github/geo-biodiversity-dataset/dataset/csv/seperate"

process_sats(input_path_raw, output_path, csv_path)
