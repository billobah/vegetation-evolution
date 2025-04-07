import duckdb
import numpy as np
import rasterio
import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "bdd", "ndvi.duckdb")

def calculate_ndvi(b3, b4):
    np.seterr(divide='ignore', invalid='ignore')
    ndvi = (b4.astype(float) - b3.astype(float)) / (b4 + b3)
    ndvi = np.nan_to_num(ndvi)
    return ndvi

def standardize_and_compute_ndvi(con):
    print("Calcul du NDVI...")

    con.execute("""
        CREATE TABLE IF NOT EXISTS standardized_ndvi (
            scene_id TEXT PRIMARY KEY,
            ndvi_array BLOB,
            width INT,
            height INT
        );
    """)

    scenes = con.execute("SELECT scene_id, b3_crop_path, b4_crop_path FROM cropped_images").fetchall()

    for scene_id, b3_crop_path, b4_crop_path in scenes:
        try:
            with rasterio.open(b3_crop_path) as src:
                b3 = src.read(1)
            with rasterio.open(b4_crop_path) as src:
                b4 = src.read(1)

            min_height = min(b3.shape[0], b4.shape[0])
            min_width = min(b3.shape[1], b4.shape[1])

            b3 = b3[:min_height, :min_width]
            b4 = b4[:min_height, :min_width]

            ndvi = calculate_ndvi(b3, b4)

            ndvi_bytes = ndvi.astype(np.float32).tobytes()

            con.execute("""
                INSERT OR REPLACE INTO standardized_ndvi 
                VALUES (?, ?, ?, ?)
            """, (scene_id, ndvi_bytes, min_width, min_height))

        except Exception as e:
            print(f"Erreur NDVI pour {scene_id} : {e}")

    print("NDVI standardisé calculé.")

if __name__ == "__main__":
    con = duckdb.connect(DB_PATH)
    standardize_and_compute_ndvi(con)
    con.close()
