import os
import shutil
from pathlib import Path

# Base directory = /src
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
RAW_DIR = os.path.join(BASE_DIR, "data", "raw", "landsat")
EXTRACT_DIR = os.path.join(BASE_DIR, "data", "raw", "extract")

def extract_images():
    """
    Décompresse les archives .tar dans le dossier 'extract'.
    """
    print("Extraction des images Landsat...")

    os.makedirs(EXTRACT_DIR, exist_ok=True)
    raw_path = Path(RAW_DIR)

    for file_path in raw_path.glob("*.tar"):
        try:
            shutil.unpack_archive(str(file_path), EXTRACT_DIR)
            print(f"{file_path.name} extrait.")
        except Exception as e:
            print(f"Erreur lors de l'extraction de {file_path.name} : {e}")

    print("Extraction terminée.")

if __name__ == "__main__":
    extract_images()
