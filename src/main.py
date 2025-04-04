from utils import telechargement_scenes
from utils import extraction_images
from utils import chemin_images
from utils import crop_straighten_images
from utils import images_to_process
from ndvi import compute_ndvi
from ndvi import ndvi_storage
from ndvi import analyze_ndvi  # à activer plus tard si besoin

def run_pipeline():
    print("=== Pipeline NDVI : Démarrage ===")

    # 1. Téléchargement des scènes satellites (commenté si déjà fait)
    # download_path = telechargement_scenes.main()

    # 2. Extraction des fichiers .TIF depuis les archives (commenté si déjà fait)
    # extract_path = "../data/raw/extract"
    # extraction_images.main(download_path, extract_path)

    # 3. Indexation des images extraites dans la BDD
    # chemin_images.main(extract_path)

    # 4. Détection des scènes à traiter (B3/B4 présents mais NDVI manquant)
    scenes = images_to_process.main()

    # 5. Crop central dynamique des B3/B4 → fichiers dans ../data/cropped
    cropped_scenes = crop_straighten_images.main(crop_ratio=0.5)

    # 6. Calcul des NDVI → fichiers GeoTIFF dans ../data/ndvi
    ndvi_series = compute_ndvi.main(cropped_scenes)

    # 7. Sauvegarde des NDVI (.npy + .png) et enregistrement dans DuckDB
    ndvi_storage.main(ndvi_series)

    # 8. Analyse NDVI (moyenne, % pixels verts, etc.) — à activer plus tard
    # analyze_ndvi.main(ndvi_series)

    print("=== Pipeline NDVI : Terminé ===")

if __name__ == "__main__":
    run_pipeline()
