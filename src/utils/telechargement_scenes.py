import logging
from src.m2m_api.api import M2M

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

# Main Function
def main():
    print("Recherche et téléchargement des scènes")
    scenes = m2m.searchScenes(**params)
    downloadMeta = m2m.retrieveScenes(params["datasetName"], scenes)
    print("Vérification du format des fichiers téléchargés")
    logging.info(f"Fichiers téléchargés : {downloadMeta}")

    # Return du chemin de téléchargement
    download_dir = "../../data/raw/landsat"
    return download_dir
