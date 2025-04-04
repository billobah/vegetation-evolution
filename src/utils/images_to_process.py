import duckdb
import os
from typing import List, Dict

def get_images_to_process(db_path: str = 'bdd/ndvi.duckdb') -> List[Dict[str, str]]:
    """
    Renvoie une liste de scènes dont les images B3/B4 sont disponibles mais
    qui n'ont pas encore été vectorisées (non présentes dans images_with_ndvi).
    """
    # Vérification existence fichier
    if not os.path.exists(db_path):
        print(f"Base {db_path} introuvable, elle sera créée.")

    try:
        con = duckdb.connect(db_path)
    except Exception as e:
        raise RuntimeError(f"Erreur lors de l'ouverture de la base DuckDB '{db_path}': {e}")

    # Création de la table d'index NDVI si absente
    con.execute("""
        CREATE TABLE IF NOT EXISTS images_with_ndvi (
            scene_id TEXT PRIMARY KEY,
            ndvi_path TEXT,
            date_processed TIMESTAMP
        );
    """)

    query = """
    SELECT 
        split_part(B3.filename, '_B3.TIF', 1) AS scene_id,
        B3.image_path AS b3,
        B4.image_path AS b4
    FROM 
        new_downloads B3
    JOIN 
        new_downloads B4
    ON 
        split_part(B3.filename, '_B3.TIF', 1) = split_part(B4.filename, '_B4.TIF', 1)
    WHERE 
        B3.band = 'B3'
        AND B4.band = 'B4'
        AND scene_id NOT IN (SELECT scene_id FROM images_with_ndvi)
    """

    results = con.execute(query).fetchall()
    con.close()

    return [
        {'scene_id': r[0], 'b3': r[1], 'b4': r[2]}
        for r in results
    ]

def main() -> List[Dict[str, str]]:
    scenes_to_process = get_images_to_process()
    print(f"🛰️ {len(scenes_to_process)} scène(s) à traiter :")
    for scene in scenes_to_process:
        print(f" - {scene['scene_id']} (B3: {scene['b3']}, B4: {scene['b4']})")

    return scenes_to_process
