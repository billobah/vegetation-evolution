import os
import numpy as np
import duckdb
from datetime import datetime
from pathlib import Path
import rasterio
import matplotlib.pyplot as plt

NDVI_FOLDER = "../data/ndvi"
DB_PATH = "bdd/ndvi.duckdb"

def save_colored_ndvi(ndvi_array: np.ndarray, output_path: str):
    """
    Sauvegarde une visualisation couleur de la matrice NDVI au format PNG.
    """
    plt.figure(figsize=(4, 4), dpi=100)
    plt.axis('off')
    plt.imshow(ndvi_array, cmap="RdYlGn", vmin=-1, vmax=1)
    plt.tight_layout(pad=0)
    plt.savefig(output_path, bbox_inches='tight', pad_inches=0)
    plt.close()

def store_ndvi(scene_id: str, ndvi_array: np.ndarray, ndvi_folder: str = NDVI_FOLDER, db_path: str = DB_PATH):
    """
    Sauvegarde la matrice NDVI au format .npy et l'image couleur .png, et enregistre la scène dans la base DuckDB.
    """
    Path(ndvi_folder).mkdir(parents=True, exist_ok=True)

    npy_path = os.path.join(ndvi_folder, f"{scene_id}_ndvi.npy")
    png_path = os.path.join(ndvi_folder, f"{scene_id}_ndvi.png")

    # Sauvegarde des fichiers
    np.save(npy_path, ndvi_array)
    save_colored_ndvi(ndvi_array, png_path)

    # Enregistrement dans DuckDB
    con = duckdb.connect(db_path)
    con.execute("""
        CREATE TABLE IF NOT EXISTS images_with_ndvi (
            scene_id TEXT PRIMARY KEY,
            ndvi_path TEXT,
            date_processed TIMESTAMP
        );
    """)
    con.execute("""
        INSERT OR REPLACE INTO images_with_ndvi VALUES (?, ?, ?)
    """, (scene_id, npy_path, datetime.now()))
    con.close()

    print(f"NDVI sauvegardé pour {scene_id} (.npy + .png) et enregistré dans DuckDB.")

def main(ndvi_series: list[dict]):
    """
    Parcourt les scènes NDVI, charge les .tif, génère .npy et .png, et les stocke avec insertion en base.
    """
    for scene in ndvi_series:
        scene_id = scene["scene_id"]
        ndvi_path = scene["ndvi_path"]

        try:
            with rasterio.open(ndvi_path) as src:
                ndvi_array = src.read(1).astype(np.float32)

            store_ndvi(scene_id, ndvi_array)
        except Exception as e:
            print(f"Erreur de stockage NDVI pour {scene_id} : {e}")
