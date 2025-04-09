import os
import duckdb

# Définir le chemin de la base DuckDB
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "bdd", "ndvi.duckdb")

# Importer les fonctions
from utils.create_downloads_table import create_downloads_table
from utils.crop_images import crop_and_store_images
from utils.standardize_and_compute_ndvi import standardize_and_compute_ndvi
from utils.store_ndvi_array import store_ndvi_array

def main():
    print("Lancement du pipeline NDVI...")

    # Connexion unique à DuckDB
    con = duckdb.connect(DB_PATH)

    # Exécution séquentielle
    create_downloads_table(con)
    crop_and_store_images(con)
    standardize_and_compute_ndvi(con)
    store_ndvi_array(con)

    con.close()

    print("Pipeline complet terminé avec succès.")

if __name__ == "__main__":
    main()
