# Import Libraries
import os
import json
import tarfile
import requests
import sys
from dotenv import load_dotenv
from authentication import authenticate

# Charger les variables d'environnement depuis .env
load_dotenv()

# Récupérer l'API Key depuis le fichier .env
API_KEY = os.getenv('USGS_API_KEY')
USER_NAME = os.getenv("USGS_USERNAME")
SERVICE_URL = "https://m2m.cr.usgs.gov/api/api/json/stable/"
LOGIN_URL = SERVICE_URL + "login-token"

# API URLs
M2M_URL = "https://m2m.cr.usgs.gov/api/api/json/stable/"
SEARCH_URL = M2M_URL + "scene-search"
DOWNLOAD_URL = M2M_URL + "download-request"

api_key = authenticate(user_name=USER_NAME, api_key=API_KEY, login_url=LOGIN_URL)
# Headers avec l'API Key
HEADERS = {"X-Auth-Token": api_key}

# Fonction pour envoyer une requête API
def send_request(url, payload):
    """Envoie une requête API POST et retourne la réponse JSON."""
    print(f"\nEnvoi de la requête API à {url} avec le payload : {json.dumps(payload, indent=2)}")
    
    response = requests.post(url, json=payload, headers=HEADERS)

    if response.status_code != 200:
        print(f"Erreur API ({url}) : {response.text}")
        return None

    try:
        data = response.json()
        print(f"Réponse brute de l'API : {json.dumps(data, indent=2)}")  # 🔥 Debugging info

        if not isinstance(data, dict):  
            print(f"Réponse inattendue de l'API : {data}")
            return None
        return data
    except json.JSONDecodeError:
        print("Erreur lors de la conversion JSON.")
        return None

# Requête de recherche d'images Landsat 7 ETM+ Collection 2 Level-2
search_payload = {
    "datasetName": "LANDSAT_ETM_C2_L2",  # Landsat 7 ETM+ C2 L2 (contient B3 et B4)
    "spatialFilter": {
        "filterType": "mbr",
        "lowerLeft": {"latitude": 8.5, "longitude": -9.5},
        "upperRight": {"latitude": 9.8, "longitude": -8.2}
    },
    "temporalFilter": {
        "startDate": "1999-07-23",
        "endDate": "2025-12-31"
    },
    "maxResults": 10,
    "cloudCoverFilter": {"max": 10, "min": 0},
}

# Recherche des scènes disponibles
results = send_request(SEARCH_URL, search_payload)

if not results or "data" not in results or "results" not in results["data"]:
    print("Aucune donnée trouvée ou erreur API.")
    sys.exit()
#
# scenes = results["data"]["results"]
#
# # Vérification que scenes est bien une liste
# if not isinstance(scenes, list):
#     print(f"Erreur : `scenes` devrait être une liste mais a le type {type(scenes)}.")
#     print("Contenu de scenes :", json.dumps(scenes, indent=2))  # Debugging
#     sys.exit()
#
# print(f"{len(scenes)} scènes trouvées.")
#
# # Création du dossier pour les téléchargements
# output_dir = '../data/raw/landsat'
# os.makedirs(output_dir, exist_ok=True)
#
# # Fonction pour extraire uniquement les bandes B3 et B4
# def extract_b3_b4(tar_path, dest_dir):
#     """Extrait les bandes B3 (Rouge) et B4 (NIR) d'une archive TAR."""
#     with tarfile.open(tar_path, 'r') as tar:
#         members = tar.getmembers()
#         b3_b4_members = [m for m in members if m.name.endswith('_B3.TIF') or m.name.endswith('_B4.TIF')]
#
#         if b3_b4_members:
#             tar.extractall(path=dest_dir, members=b3_b4_members)
#             print(f"Bandes B3 et B4 extraites dans : {dest_dir}")
#         else:
#             print(f"Aucune bande B3 ou B4 trouvée dans : {tar_path}")
#
# # Téléchargement des images
# for scene in scenes:
#     if not isinstance(scene, dict):
#         print(f"Erreur : `scene` n'est pas un dictionnaire mais {type(scene)}")
#         continue
#
#     entity_id = scene.get('entityId')
#     display_id = scene.get('displayId')  # Contient la date sous format YYYYMMDD
#
#     # Extraction de la date depuis displayId (ex: "LE07_L2SP_119052_20240119_20240215_02_T2")
#     acquisition_date = None
#     if display_id and len(display_id) > 20:
#         acquisition_date = display_id.split("_")[3]  # Extrait la partie YYYYMMDD
#         acquisition_date = f"{acquisition_date[:4]}-{acquisition_date[4:6]}-{acquisition_date[6:]}"  # Convertir en YYYY-MM-DD
#
#     if not acquisition_date or not entity_id:
#         print("❌ Données de scène manquantes, passage à la suivante.")
#         continue
#
#     print(f"\n✅ Téléchargement de la scène : {entity_id} pour la date : {acquisition_date}")
#
#     # Création d'un dossier par date
#     date_dir = os.path.join(output_dir, acquisition_date)
#     os.makedirs(date_dir, exist_ok=True)
#
#     # Demande de téléchargement
#     download_payload = {
#         "downloads": [{"entityId": entity_id, "productId": entity_id, "datasetName": "landsat_etm_c2_l2"}]
#     }
#     download_results = send_request(DOWNLOAD_URL, download_payload)
#
#     if not download_results or "data" not in download_results:
#         print(f"Erreur lors de la demande de téléchargement pour la scène {entity_id}.")
#         continue
#
#     download_url = download_results["data"][0]["url"]
#
#     # Téléchargement du fichier
#     tar_path = os.path.join(date_dir, f"{entity_id}.tar")
#     response = requests.get(download_url, stream=True)
#     with open(tar_path, "wb") as file:
#         for chunk in response.iter_content(chunk_size=8192):
#             file.write(chunk)
#
#     print(f"Téléchargement terminé : {tar_path}")
#
#     # Extraction des bandes B3 et B4
#     extract_b3_b4(tar_path, date_dir)
#
# print("\nTéléchargements terminés et images organisées par date.")