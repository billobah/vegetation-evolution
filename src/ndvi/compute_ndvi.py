import os
import numpy as np
import matplotlib.pyplot as plt
import rasterio
from glob import glob

# Dossiers
cropped_dir = '../../data/cropped_straightened'
ndvi_output_dir = '../../results/ndvi_results_cropped_straightened_images'
os.makedirs(ndvi_output_dir, exist_ok=True)

# Recadrage
def crop_to_same_size(image1, image2):
    min_rows = min(image1.shape[0], image2.shape[0])
    min_cols = min(image1.shape[1], image2.shape[1])
    return image1[:min_rows, :min_cols], image2[:min_rows, :min_cols]

# Calcul NDVI
def calculate_ndvi(red, nir):
    return np.where((nir + red) == 0., 0, (nir - red) / (nir + red))

# Sauvegarde image NDVI
def calculate_and_save_ndvi(ndvi: np.ndarray, image_name: str):
    save_path = os.path.join(ndvi_output_dir, image_name.replace('.TIF', '_ndvi.png'))
    plt.figure(figsize=(10, 8))
    plt.imshow(ndvi, cmap='RdYlGn', vmin=-1, vmax=1)
    plt.colorbar(label='NDVI Value')
    plt.title(f'NDVI Map - {image_name}')
    plt.savefig(save_path)
    plt.close()
    print(f"NDVI image saved: {save_path}")

# Lecture bande unique
def load_band(image_path):
    with rasterio.open(image_path) as src:
        return src.read(1).astype('float32')

# Traitement BATCH NDVI
def process_images(cropped_dir):
    ndvi_series = {}

    b3_files = sorted(glob(os.path.join(cropped_dir, '*_B3_Rouge_cropped_straightened.TIF')))
    b4_files = sorted(glob(os.path.join(cropped_dir, '*_B4_NIR_cropped_straightened.TIF')))

    if not b3_files or not b4_files:
        print("Aucun fichier B3 ou B4 trouvé dans le dossier.")
        return ndvi_series

    for b3_path, b4_path in zip(b3_files, b4_files):
        b3_name = os.path.basename(b3_path)
        b4_name = os.path.basename(b4_path)

        if not os.path.isfile(b3_path) or not os.path.isfile(b4_path):
            print(f"Fichier manquant : {b3_name} ou {b4_name}")
            continue

        print(f"\nTraitement NDVI pour : {b3_name}")

        red = load_band(b3_path)
        nir = load_band(b4_path)

        red_cropped, nir_cropped = crop_to_same_size(red, nir)
        ndvi = calculate_ndvi(red_cropped, nir_cropped)

        ndvi_series[b3_name] = ndvi  # clé = nom complet avec .TIF
        calculate_and_save_ndvi(ndvi, b3_name)

    print(f"\nNombre total d'images traitées : {len(ndvi_series)}")
    return ndvi_series


def main(cropped_dir):
    ndvi_series = process_images(cropped_dir)
    print("\nCalcul du NDVI terminé.")
    return ndvi_series
