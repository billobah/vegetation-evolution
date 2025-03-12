# Import Libraries
import os
import json
import tarfile
import requests
import sys
from dotenv import load_dotenv
from authentication import authenticate
from api import M2M  # Importation de la classe M2M depuis le projet GitHub

# Charger les variables d'environnement depuis .env
load_dotenv()

# Récupérer l'API Key depuis le fichier .env
TOKEN_KEY = os.getenv('USGS_TOKEN')
USER_NAME = os.getenv("USGS_USERNAME")
SERVICE_URL = "https://m2m.cr.usgs.gov/api/api/json/stable/"
LOGIN_URL = SERVICE_URL + "login-token"

# API URLs
M2M_URL = "https://m2m.cr.usgs.gov/api/api/json/stable/"
SEARCH_URL = M2M_URL + "scene-search"
DOWNLOAD_URL = M2M_URL + "download-request"

api_key = authenticate(user_name=USER_NAME, token_value=TOKEN_KEY, login_url=LOGIN_URL)
HEADERS = {"X-Auth-Token": api_key}

# Fonction pour envoyer une requête API
def send_request(url, payload):
    """Envoie une requête API POST et retourne la réponse JSON."""
    print(f"\n🔎 Envoi de la requête API à {url}...")
    
    response = requests.post(url, json=payload, headers=HEADERS)

    if response.status_code != 200:
        print(f"❌ Erreur API ({url}) : {response.text}")
        return None

    try:
        data = response.json()
        return data
    except json.JSONDecodeError:
        print("❌ Erreur lors de la conversion JSON.")
        return None

# Recherche d'images Landsat
search_payload = {
    "datasetName": "LANDSAT_ETM_C2_L2",  
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

results = send_request(SEARCH_URL, search_payload)

if not results or "data" not in results or "results" not in results["data"]:
    print("❌ Aucune donnée trouvée ou erreur API.")
    sys.exit()

scenes = results["data"]["results"]

if not isinstance(scenes, list):
    print(f"❌ Erreur : `scenes` devrait être une liste mais est de type {type(scenes)}.")
    sys.exit()

print(f"✅ {len(scenes)} scènes trouvées.")

# Création du dossier pour les téléchargements
output_dir = 'data/raw/landsat'
os.makedirs(output_dir, exist_ok=True)

# Fonction pour extraire uniquement les bandes B3 et B4
def extract_b3_b4(tar_path, dest_dir):
    """Extrait les bandes B3 (Rouge) et B4 (NIR) d'une archive TAR."""
    with tarfile.open(tar_path, 'r') as tar:
        members = tar.getmembers()
        b3_b4_members = [m for m in members if '_B3.TIF' in m.name or '_B4.TIF' in m.name]

        if b3_b4_members:
            tar.extractall(path=dest_dir, members=b3_b4_members)
            print(f"📂 Bandes B3 et B4 extraites dans : {dest_dir}")
        else:
            print(f"⚠️ Aucune bande B3 ou B4 trouvée dans : {tar_path}")

# Téléchargement des images
for scene in scenes:
    if not isinstance(scene, dict):
        print(f"❌ Erreur : `scene` n'est pas un dictionnaire mais {type(scene)}")
        continue

    entity_id = scene.get('entityId')
    display_id = scene.get('displayId')

    # Extraction de la date au format YYYY-MM-DD
    acquisition_date = None
    if display_id and len(display_id) > 20:
        acquisition_date = display_id.split("_")[3]  
        acquisition_date = f"{acquisition_date[:4]}-{acquisition_date[4:6]}-{acquisition_date[6:]}"  

    if not acquisition_date or not entity_id:
        print("⚠️ Données de scène manquantes, passage à la suivante.")
        continue

    print(f"\n📥 Téléchargement de la scène : {entity_id} - Date : {acquisition_date}")

    # Création d'un dossier par date
    date_dir = os.path.join(output_dir, acquisition_date)
    os.makedirs(date_dir, exist_ok=True)

    # Demande de téléchargement
    download_payload = {
        "downloads": [{"entityId": entity_id, "productId": entity_id, "datasetName": "landsat_etm_c2_l2"}]
    }
    download_results = send_request(DOWNLOAD_URL, download_payload)

    # Vérification de la structure de réponse
    if not download_results or "data" not in download_results:
        print(f"⚠️ Erreur lors de la demande de téléchargement pour la scène {entity_id}.")
        print(f"Réponse de l'API : {json.dumps(download_results, indent=2)}")
        continue

    if not isinstance(download_results["data"], list) or not download_results["data"]:
        print(f"⚠️ Aucune donnée de téléchargement disponible pour la scène {entity_id}.")
        continue

    # Vérification que la clé "url" existe bien
    first_download = download_results["data"][0]
    if "url" not in first_download:
        print(f"⚠️ La clé 'url' est absente dans la réponse de téléchargement pour {entity_id}.")
        print(f"Réponse API : {json.dumps(first_download, indent=2)}")
        continue

    download_url = first_download["url"]

    # Téléchargement du fichier
    tar_path = os.path.join(date_dir, f"{entity_id}.tar")
    try:
        response = requests.get(download_url, stream=True)
        response.raise_for_status()
        with open(tar_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)

        print(f"✅ Téléchargement terminé : {tar_path}")

        # Extraction des bandes B3 et B4
        extract_b3_b4(tar_path, date_dir)

    except requests.RequestException as e:
        print(f"❌ Erreur lors du téléchargement de {entity_id} : {e}")

print("\n✅ Téléchargements terminés et images organisées par date.")
