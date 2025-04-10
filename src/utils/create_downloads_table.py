import os
import duckdb
from pathlib import Path
import rasterio
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "bdd", "ndvi.duckdb")


def create_downloads_table(con):
    extract_path = os.path.join(BASE_DIR, "data", "raw", "extract")

    con.execute("""
        CREATE OR REPLACE TABLE downloads (
            filename TEXT,
            band TEXT,
            date_downloaded TIMESTAMP,
            image_path TEXT,
            width INT,
            height INT,
            PRIMARY KEY(filename, band)
        );
    """)

    extract_path_obj = Path(extract_path)
    paths_to_images = list(extract_path_obj.rglob("*_B3.TIF")) + list(extract_path_obj.rglob("*_B4.TIF"))

    for path in paths_to_images:
        with rasterio.open(path) as src:
            width, height = src.width, src.height

        filename = path.name
        band = 'B3' if '_B3' in filename else 'B4'
        con.execute("""
            INSERT OR IGNORE INTO downloads VALUES (?, ?, ?, ?, ?, ?)
        """, (filename, band, datetime.now(), str(path.resolve()), width, height))


if __name__ == "__main__":
    con = duckdb.connect(DB_PATH)
    create_downloads_table(con)
    con.close()
