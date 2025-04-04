import os
import numpy as np
import rasterio

NDVI_OUTPUT_DIR = "../data/ndvi"

def calculate_ndvi(b3: np.ndarray, b4: np.ndarray) -> np.ndarray:
    """
    Calcule l'indice NDVI à partir des bandes B3 et B4.
    """
    np.seterr(divide='ignore', invalid='ignore')  # éviter division par zéro
    denominator = b4 + b3
    ndvi = np.where(denominator == 0, 0, (b4 - b3) / denominator)
    return ndvi.astype(np.float32)

def save_ndvi_image(ndvi: np.ndarray, output_path: str):
    """
    Sauvegarde l'image NDVI en GeoTIFF (sans géoréférencement).
    """
    with rasterio.open(
        output_path,
        'w',
        driver='GTiff',
        height=ndvi.shape[0],
        width=ndvi.shape[1],
        count=1,
        dtype=ndvi.dtype,
        crs='+proj=latlong',
        transform=rasterio.Affine.identity()
    ) as dst:
        dst.write(ndvi, 1)

def main(cropped_scenes: list[dict]) -> list[dict]:
    """
    Pour chaque scène cropée, calcule le NDVI et le sauvegarde au format GeoTIFF.
    Retourne une liste de dictionnaires avec scene_id et chemin NDVI.
    """
    os.makedirs(NDVI_OUTPUT_DIR, exist_ok=True)
    ndvi_results = []

    for scene in cropped_scenes:
        scene_id = scene["scene_id"]
        b3_path = scene["b3_crop"]
        b4_path = scene["b4_crop"]

        try:
            with rasterio.open(b3_path) as src:
                b3 = src.read(1).astype(np.float32)
            with rasterio.open(b4_path) as src:
                b4 = src.read(1).astype(np.float32)

            ndvi = calculate_ndvi(b3, b4)
            ndvi_path = os.path.join(NDVI_OUTPUT_DIR, f"{scene_id}_ndvi.tif")

            save_ndvi_image(ndvi, ndvi_path)

            ndvi_results.append({
                "scene_id": scene_id,
                "ndvi_path": ndvi_path
            })

            print(f"NDVI généré et sauvegardé : {ndvi_path}")

        except Exception as e:
            print(f"Erreur NDVI pour {scene_id} : {e}")

    return ndvi_results
