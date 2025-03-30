import os
import re
import tarfile
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Répertoires par défaut (modifiable lors de l'appel à main)
download_dir = "../data/raw/landsat"
extract_dir = "../data/raw/extract"

# Fonction pour extraire la date du nom de fichier
def extract_date_from_filename(filename):
    match = re.search(r"^[^_]+_[^_]+_[^_]+_(\d{8})_", filename)
    return match.group(1) if match else None

# Fonction pour extraire uniquement les bandes B3 et B4
def extract_bands_from_tar(tar_path, extract_dir):
    filename = os.path.basename(tar_path)
    date_str = extract_date_from_filename(filename)

    if not date_str:
        logging.warning(f"Impossible d'extraire la date pour {filename}, fichier ignoré.")
        return

    output_dir = os.path.join(extract_dir, date_str)

    # Vérifie si déjà traité
    if os.path.exists(output_dir) and any(f.endswith(("B3.TIF", "B4.TIF")) for f in os.listdir(output_dir)):
        logging.info(f"Archive déjà traitée ({filename}), images B3/B4 déjà extraites.")
        return

    os.makedirs(output_dir, exist_ok=True)

    try:
        with tarfile.open(tar_path, "r:*") as tar:
            members_to_extract = [m for m in tar.getmembers() if "B3.TIF" in m.name or "B4.TIF" in m.name]

            if not members_to_extract:
                logging.warning(f"Aucune bande B3 ou B4 trouvée dans {filename}")
                return

            for member in members_to_extract:
                logging.info(f"Extraction de {member.name} vers {output_dir}")
                tar.extract(member, output_dir)

                # Renommage à plat
                extracted_path = os.path.join(output_dir, member.name)
                new_path = os.path.join(output_dir, os.path.basename(member.name))
                if extracted_path != new_path:
                    os.rename(extracted_path, new_path)

        logging.info(f"Extraction réussie pour {filename}")

    except Exception as e:
        logging.error(f"Erreur lors du traitement de {filename} : {e}")

# Fonction principale à appeler depuis un autre script
def main(download_dir, extract_dir):
    logging.info("Début traitement des archives TAR")

    for file in os.listdir(download_dir):
        tar_path = os.path.join(download_dir, file)
        if os.path.isfile(tar_path) and tar_path.endswith(".tar"):
            logging.info(f"Traitement de l'archive : {tar_path}")
            extract_bands_from_tar(tar_path, extract_dir)

    logging.info("Suppression des fichiers .tar.size inutiles")
    for file in os.listdir(download_dir):
        size_file_path = os.path.join(download_dir, file)
        if file.endswith(".tar.size"):
            os.remove(size_file_path)
            logging.info(f"Fichier supprimé : {size_file_path}")

    logging.info("Extraction et organisation terminées.")

    return extract_dir
