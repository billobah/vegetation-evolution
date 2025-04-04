import os
import numpy as np
import rasterio
from rasterio.enums import Resampling
from utils import images_to_process

CROPPED_OUTPUT_DIR = "../data/cropped"

def load_and_crop_center(image_path: str, crop_ratio: float = 0.5) -> np.ndarray:
    """
    Charge une image .TIF et effectue un crop central carré dynamique.
    Le crop_size est défini comme un pourcentage (crop_ratio) de la plus petite dimension.
    """
    with rasterio.open(image_path) as src:
        img = src.read(1, resampling=Resampling.bilinear)
        h, w = img.shape
        crop_size = int(min(h, w) * crop_ratio)

        if crop_size < 32:
            raise ValueError(f"Le crop_size est trop petit ({crop_size} pixels) pour {image_path}")

        center_h, center_w = h // 2, w // 2
        half_crop = crop_size // 2

        cropped = img[
            center_h - half_crop: center_h + half_crop,
            center_w - half_crop: center_w + half_crop
        ]
        return cropped.astype(np.float32)

def preprocess_image(b3_path: str, b4_path: str, crop_ratio: float = 0.5) -> tuple[np.ndarray, np.ndarray]:
    """
    Applique un crop central dynamique sur les deux images B3 et B4.
    """
    b3 = load_and_crop_center(b3_path, crop_ratio)
    b4 = load_and_crop_center(b4_path, crop_ratio)
    return b3, b4

def save_cropped_image(array: np.ndarray, output_path: str):
    """
    Sauvegarde une image numpy en format GeoTIFF sans géoréférencement.
    """
    with rasterio.open(
        output_path,
        'w',
        driver='GTiff',
        height=array.shape[0],
        width=array.shape[1],
        count=1,
        dtype=array.dtype,
        crs='+proj=latlong',
        transform=rasterio.Affine.identity()
    ) as dst:
        dst.write(array, 1)

def main(crop_ratio: float = 0.5) -> list[dict]:
    """
    Traite toutes les images détectées (via images_to_process) et sauvegarde les crops.
    Retourne la liste des scènes cropées.
    """
    os.makedirs(CROPPED_OUTPUT_DIR, exist_ok=True)

    scenes = images_to_process.main()
    processed = []

    for scene in scenes:
        scene_id = scene["scene_id"]
        b3_path = scene["b3"]
        b4_path = scene["b4"]

        try:
            b3_crop, b4_crop = preprocess_image(b3_path, b4_path, crop_ratio)

            b3_output = os.path.join(CROPPED_OUTPUT_DIR, f"{scene_id}_B3_crop.tif")
            b4_output = os.path.join(CROPPED_OUTPUT_DIR, f"{scene_id}_B4_crop.tif")

            save_cropped_image(b3_crop, b3_output)
            save_cropped_image(b4_crop, b4_output)

            processed.append({
                "scene_id": scene_id,
                "b3_crop": b3_output,
                "b4_crop": b4_output
            })

            print(f"{scene_id} cropé et sauvegardé.")
        except Exception as e:
            print(f"Erreur pour {scene_id} : {e}")

    return processed
