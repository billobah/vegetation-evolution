from utils import telechargement_scenes
from utils import extraction_images
from utils import crop_straighten_images
from ndvi import compute_ndvi
from ndvi import analyze_ndvi


def run_pipeline():
    print("=== Pipeline NDVI : Démarrage ===")

    # 1. Téléchargement
    download_path = telechargement_scenes.main()

    # 2. Extraction des images
    extract_path = "../data/raw/extract"  # On fixe explicitement le dossier d'extraction
    extraction_images.main(download_path, extract_path)

    # 3. Découpage et redressement
    # cropped_path = crop_straighten_images.main(extract_path)

    # 4. Calcul NDVI
    # ndvi_series = compute_ndvi.main(cropped_path)

    # 5. Analyse NDVI
    # analyze_ndvi.main(ndvi_series)

    print("=== Pipeline NDVI : Terminé ===")


if __name__ == "__main__":
    run_pipeline()
