from utils import telechargement_scenes
from utils import extraction_images
from utils import crop_straighten_images
from ndvi import compute_ndvi
from ndvi import analyze_ndvi
from ndvi import vectorize_images


def run_pipeline():
    print("=== Pipeline NDVI : Démarrage ===")

    # 1. Téléchargement
    #download_path = telechargement_scenes.main()

    # 2. Extraction des images
    #extraction_images.main(download_path)

    # 3. Découpage et redressement
    cropped_path = crop_straighten_images.main()

    # 4. Calcul NDVI
    ndvi_series = compute_ndvi.main(cropped_path)

    # 5. Analyse NDVI
    analyze_ndvi.main(ndvi_series)

    # 6. Vectorisation et export
    vectorize_images.main(
        cropped_path=cropped_path,
        ndvi_series=ndvi_series,
        db_path="../bdd/image_vectors.duckdb",
        table_name="ndvi_vectors_wide",
        export_dir="../bdd"
    )

    print("=== Pipeline NDVI : Terminé ===")


if __name__ == "__main__":
    run_pipeline()