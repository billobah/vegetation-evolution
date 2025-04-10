import os
import logging
import duckdb

# Importer les modules du pipeline
from utils.create_downloads_table import create_downloads_table
from utils.crop_images import crop_and_store_images
from utils.standardize_and_compute_ndvi import standardize_and_compute_ndvi

# === Configuration du Logging ===
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)

# === Définition des chemins ===
# Point de départ = src/
BASE_DIR = os.path.dirname(__file__)
DB_DIR = os.path.join(BASE_DIR, "bdd")       # ➔ src/bdd/
DB_PATH = os.path.join(DB_DIR, "ndvi.duckdb") # ➔ src/bdd/ndvi.duckdb

# === Fonction principale ===
def run_pipeline():
    logging.info("=== Pipeline NDVI : Démarrage ===")

    # 1. S'assurer que le dossier 'src/bdd' existe
    os.makedirs(DB_DIR, exist_ok=True)
    logging.info(f"Dossier de la base de données : {DB_DIR}")

    # 2. Supprimer l'ancienne base si elle existe AVANT connexion
    if os.path.exists(DB_PATH):
        logging.warning(f"Ancienne base détectée : suppression {DB_PATH}")
        os.remove(DB_PATH)

    # 3. Ouvrir une nouvelle connexion propre
    con = duckdb.connect(DB_PATH)
    logging.info(f"Connexion ouverte à la base : {DB_PATH}")

    try:
        # 4. Pipeline d'exécution
        logging.info("Étape 1 : Création de la table downloads...")
        create_downloads_table(con)

        logging.info("Étape 2 : Crop et enregistrement des images...")
        crop_and_store_images(con)

        logging.info("Étape 3 : Calcul et standardisation du NDVI...")
        standardize_and_compute_ndvi(con)

    except Exception as e:
        logging.exception(f"Erreur critique pendant l'exécution du pipeline : {e}")

    finally:
        con.close()
        logging.info("Connexion à la base fermée.")

    logging.info("=== Pipeline NDVI : Terminé avec succès ===")

# === Point d'entrée ===
if __name__ == "__main__":
    run_pipeline()
