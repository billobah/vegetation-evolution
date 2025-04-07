import duckdb
import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "bdd", "ndvi.duckdb")

def store_ndvi_array(con):
    print("Stockage final des NDVI...")

    con.execute("""
        CREATE TABLE IF NOT EXISTS ndvi_array (
            scene_id TEXT PRIMARY KEY,
            ndvi_values BLOB
        );
    """)

    scenes = con.execute("SELECT scene_id, ndvi_array FROM standardized_ndvi").fetchall()

    for scene_id, ndvi_array in scenes:
        try:
            con.execute("""
                INSERT OR REPLACE INTO ndvi_array 
                VALUES (?, ?)
            """, (scene_id, ndvi_array))
        except Exception as e:
            print(f"Erreur de stockage NDVI pour {scene_id} : {e}")

    print("Stockage des NDVI terminé.")

if __name__ == "__main__":
    con = duckdb.connect(DB_PATH)
    store_ndvi_array(con)
    con.close()
