import os
import re
import tarfile
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Chemin du répertoire contenant les archives TAR
download_dir = "../../data/raw/landsat"  # Met le bon chemin absolu si nécessaire


# Fonction pour extraire la date du nom de fichier
def extract_date_from_filename(filename):
    match = re.search(r"^[^_]+_[^_]+_[^_]+_(\d{8})_", filename)
    return match.group(1) if match else None


# Fonction pour extraire les bandes B3 et B4 et les organiser par date
def extract_bands_from_tar(tar_path, download_dir):
    """Extrait uniquement les bandes B3 et B4 et les organise par date."""
    filename = os.path.basename(tar_path)
    date_str = extract_date_from_filename(filename)

    if not date_str:
        logging.warning(f"Impossible d'extraire la date pour {filename}, fichier ignoré.")
        return

    output_dir = os.path.join(download_dir, date_str)

    # Vérifier si le dossier de destination existe déjà et contient des fichiers B3 et B4
    if os.path.exists(output_dir) and any(f.endswith(("B3.TIF", "B4.TIF")) for f in os.listdir(output_dir)):
        logging.info(f"Archive déjà traitée ({filename}), suppression de l'archive inutile.")
        os.remove(tar_path)  # Supprime l'archive directement
        return

    os.makedirs(output_dir, exist_ok=True)  # Créer le dossier si nécessaire

    # Ouvrir l'archive TAR
    try:
        with tarfile.open(tar_path, "r:*") as tar:  # Gestion des différents formats .tar, .tar.gz, etc.
            members_to_extract = [m for m in tar.getmembers() if "B3.TIF" in m.name or "B4.TIF" in m.name]

            if not members_to_extract:
                logging.warning(f"Aucune bande B3 ou B4 trouvée dans {filename}")
                return

            for member in members_to_extract:
                logging.info(f"Extraction de {member.name} vers {output_dir}")
                tar.extract(member, output_dir)  # Extraction directe

                # Renommer les fichiers pour éviter d’avoir des sous-dossiers
                extracted_path = os.path.join(output_dir, member.name)
                new_path = os.path.join(output_dir, os.path.basename(member.name))
                if extracted_path != new_path:
                    os.rename(extracted_path, new_path)

        # Suppression de l'archive après extraction
        os.remove(tar_path)
        logging.info(f"Archive supprimée : {tar_path}")

    except Exception as e:
        logging.error(f"Erreur lors du traitement de {filename} : {e}")

def main():
    print("Début examen dossier et traitement des archives TAR")
    for file in os.listdir(download_dir):
        tar_path = os.path.join(download_dir, file)
        if os.path.isfile(tar_path) and tar_path.endswith(".tar"):
            logging.info(f"Traitement de l'archive : {tar_path}")
            extract_bands_from_tar(tar_path, download_dir)

    print("Début suppression des fichiers .tar.size")
    for file in os.listdir(download_dir):
        size_file_path = os.path.join(download_dir, file)
        if file.endswith(".tar.size"):
            os.remove(size_file_path)
            logging.info(f"Fichier supprimé : {size_file_path}")

    logging.info("Extraction et organisation terminées.")
