import duckdb
from pathlib import Path
from datetime import datetime
import re

def main(extract_path: str, db_path: str = "bdd/ndvi.duckdb"):
    """
    Scanne les sous-dossiers de extract_path à la recherche de fichiers B3/B4
    et les enregistre dans la base DuckDB.
    """
    extract_path_obj = Path(extract_path)
    date_folder_pattern = re.compile(r"^\d{8}$")
    paths_to_images = []

    for subdir in extract_path_obj.iterdir():
        if subdir.is_dir() and date_folder_pattern.match(subdir.name):
            paths_to_images += list(subdir.glob("*_B3.TIF"))
            paths_to_images += list(subdir.glob("*_B4.TIF"))

    if not paths_to_images:
        print("Aucune image B3 ou B4 trouvée dans les sous-dossiers.")
        return

    con = duckdb.connect(db_path)
    con.execute("""
        CREATE TABLE IF NOT EXISTS downloads (
            filename TEXT,
            band TEXT,
            date_downloaded TIMESTAMP,
            image_path TEXT,
            PRIMARY KEY(filename, band)
        );
    """)

    for path in paths_to_images:
        filename = path.name
        band = 'B3' if '_B3' in filename else 'B4'
        con.execute("""
            INSERT OR IGNORE INTO downloads VALUES (?, ?, ?, ?)
        """, (filename, band, datetime.now(), str(path.resolve())))

    con.close()
    print(f"{len(paths_to_images)} images B3/B4 enregistrées dans la base.")
