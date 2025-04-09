import os
import duckdb
import numpy as np

# Définir le chemin de la base DuckDB
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "bdd", "ndvi.duckdb")

def store_ndvi_array(con):
    """
    Récupère les NDVI en BLOB, les transforme en ARRAY lisibles et les stocke.
    """
    print("Conversion et stockage final des NDVI en ARRAY...")

    # Création de la nouvelle table cible avec une colonne ARRAY
    con.execute("""
        CREATE TABLE IF NOT EXISTS ndvi_array (
            scene_id TEXT PRIMARY KEY,
            ndvi_values ARRAY<FLOAT>
        );
    """)

    # Lire tous les NDVI standardisés
    scenes = con.execute("SELECT scene_id, ndvi_array, width, height FROM standardized_ndvi").fetchall()

    for scene_id, ndvi_blob, width, height in scenes:
        try:
            # Convertir le BLOB binaire en tableau NumPy
            ndvi_array = np.frombuffer(ndvi_blob, dtype=np.float32)

            # Stocker le tableau dans DuckDB
            con.execute("""
                INSERT OR REPLACE INTO ndvi_array 
                VALUES (?, ?)
            """, (scene_id, ndvi_array.tolist()))

        except Exception as e:
            print(f"Erreur de conversion NDVI pour {scene_id} : {e}")

    print("Stockage NDVI en ARRAY terminé.")

if __name__ == "__main__":
    con = duckdb.connect(DB_PATH)
    store_ndvi_array(con)
    con.close()
