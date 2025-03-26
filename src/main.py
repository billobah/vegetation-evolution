from utils import telechargement_scenes
from utils import extraction_images
from utils import crop_straighten_images
from ndvi import compute_ndvi
from ndvi import analyze_ndvi


if __name__ == "__main__":
    # Étape 1 : téléchargement
    download_path = telechargement_scenes.main()

    # Étape 2 : extraction
    extraction_images.main(download_path)

    # Étape 3 : découpage/redressement
    cropped_path = crop_straighten_images.main()

    # Étape 4 : calcul NDVI
    ndvi_series = compute_ndvi.main(cropped_path)

    # Étape 5 : analyse NDVI
    analyze_ndvi.main(ndvi_series)