import os
import logging
from src.m2m_api.api import M2M

# ➔ Dynamique : on récupère automatiquement le dossier /src/
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
LANDSAT_DIR = os.path.join(BASE_DIR, "data/raw/landsat")

# Configuration du logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Définition des paramètres de recherche
params = {
    "datasetName": "landsat_tm_c2_l1",
    "spatialFilter": {
        "filterType": "mbr",
        "lowerLeft": {"latitude": 8.5, "longitude": -9.5},
        "upperRight": {"latitude": 9.8, "longitude": -8.2},
    },
    "temporalFilter": {"startDate": "2000-01-01", "endDate": "2024-12-31"},
    "maxResults": 10,
    "cloudCoverFilter": {"max": 10, "min": 0},
}

# Initialisation de l'API
m2m = M2M()


def main():
    print("Recherche et téléchargement des scènes")

    # Assure que le dossier existe
    os.makedirs(LANDSAT_DIR, exist_ok=True)

    scenes = m2m.searchScenes(**params)

    # On enlève download_dir car pas accepté par l'API
    downloadMeta = m2m.retrieveScenes(params["datasetName"], scenes)

    print("Vérification du format des fichiers téléchargés")
    logging.info(f"Fichiers téléchargés : {downloadMeta}")

    return LANDSAT_DIR


if __name__ == "__main__":
    main()
