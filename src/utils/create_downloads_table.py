import os
import duckdb
from pathlib import Path
import rasterio
from datetime import datetime

# Définition dynamique des chemins
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
EXTRACT_PATH = os.path.join(BASE_DIR, "data", "raw", "extract")
DB_PATH = os.path.join(BASE_DIR, "bdd", "ndvi.duckdb")

def create_downloads_table(con):
    """
    Crée la table 'downloads' et insère les métadonnées des images B3/B4.
    """
    print("Création de la table 'downloads'...")

    con.execute("""
        CREATE TABLE IF NOT EXISTS downloads (
            filename TEXT,
            band TEXT,
            date_downloaded TIMESTAMP,
            image_path TEXT,
            width INT,
            height INT,
            PRIMARY KEY(filename, band)
        );
    """)

    extract_path_obj = Path(EXTRACT_PATH)
    paths_to_images = list(extract_path_obj.rglob("*_B3.TIF")) + list(extract_path_obj.rglob("*_B4.TIF"))

    for path in paths_to_images:
        try:
            with rasterio.open(path) as src:
                width, height = src.width, src.height

            filename = path.name
            band = 'B3' if '_B3' in filename else 'B4'

            con.execute("""
                INSERT OR IGNORE INTO downloads 
                VALUES (?, ?, ?, ?, ?, ?)
            """, (filename, band, datetime.now(), str(path.resolve()), width, height))

        except Exception as e:
            print(f"Erreur lors de l'insertion de {path.name} : {e}")

    print("Table 'downloads' créée et peuplée.")

if __name__ == "__main__":
    con = duckdb.connect(DB_PATH)
    create_downloads_table(con)
    con.close()
