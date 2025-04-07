import os
import duckdb
import numpy as np
import rasterio

# Définition dynamique des chemins
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
CROPPED_DIR = os.path.join(BASE_DIR, "data", "cropped")
DB_PATH = os.path.join(BASE_DIR, "bdd", "ndvi.duckdb")

def crop_center(img: np.ndarray, crop_ratio: float = 0.5) -> np.ndarray:
    h, w = img.shape
    crop_size = int(min(h, w) * crop_ratio)
    center_h, center_w = h // 2, w // 2
    half_crop = crop_size // 2
    return img[center_h - half_crop:center_h + half_crop, center_w - half_crop:center_w + half_crop]

def crop_and_store_images(con):
    print("Cropping des images...")

    os.makedirs(CROPPED_DIR, exist_ok=True)

    con.execute("""
        CREATE TABLE IF NOT EXISTS cropped_images (
            scene_id TEXT PRIMARY KEY,
            b3_crop_path TEXT,
            b4_crop_path TEXT,
            width INT,
            height INT
        );
    """)

    scenes = con.execute("""
        SELECT DISTINCT split_part(filename, '_B3.TIF', 1) AS scene_id
        FROM downloads
        WHERE band = 'B3'
    """).fetchall()

    for (scene_id,) in scenes:
        try:
            b3_path, = con.execute("SELECT image_path FROM downloads WHERE filename LIKE ?", (scene_id + '_B3.TIF',)).fetchone()
            b4_path, = con.execute("SELECT image_path FROM downloads WHERE filename LIKE ?", (scene_id + '_B4.TIF',)).fetchone()

            with rasterio.open(b3_path) as src:
                b3 = src.read(1)
            with rasterio.open(b4_path) as src:
                b4 = src.read(1)

            b3_crop = crop_center(b3)
            b4_crop = crop_center(b4)

            output_b3 = os.path.join(CROPPED_DIR, f"{scene_id}_B3_crop.tif")
            output_b4 = os.path.join(CROPPED_DIR, f"{scene_id}_B4_crop.tif")

            for array, path in zip([b3_crop, b4_crop], [output_b3, output_b4]):
                with rasterio.open(
                    path,
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

            con.execute("""
                INSERT OR REPLACE INTO cropped_images 
                VALUES (?, ?, ?, ?, ?)
            """, (scene_id, output_b3, output_b4, b3_crop.shape[1], b3_crop.shape[0]))

        except Exception as e:
            print(f"Erreur de crop pour {scene_id} : {e}")

    print("Cropping terminé.")

if __name__ == "__main__":
    con = duckdb.connect(DB_PATH)
    crop_and_store_images(con)
    con.close()
