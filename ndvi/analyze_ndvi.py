# Import Libraries
import os
import numpy as np
import matplotlib.pyplot as plt
import rasterio
from glob import glob
import pandas as pd

# Directory Configuration
ndvi_input_dir = '../results/ndvi_results_cropped_straightened_images'
ndvi_output_dir = '../results/ndvi_results_graphs_stats'
os.makedirs(ndvi_output_dir, exist_ok=True)

# NDVI Classes
ndvi_labels = [
    "Eau", 
    "Sols Nus/Urbain", 
    "Végétation Très Faible", 
    "Végétation Faible", 
    "Végétation Modérée", 
    "Végétation Dense", 
    "Forêt Tropicale"
]

# Load NDVI Images
def load_ndvi_images():
    ndvi_series = {}
    
    # Boucle à travers les images NDVI par date
    for file in sorted(glob(os.path.join(ndvi_input_dir, '*_ndvi.png'))):
        date_str = os.path.basename(file).split('_ndvi.png')[0]
        
        # Chargement de l'image NDVI
        with rasterio.open(file) as src:
            ndvi = src.read(1).astype('float32')
            ndvi_series[date_str] = ndvi
    
    print("Images NDVI chargées avec succès.")
    return ndvi_series

# NDVI Classification
def classify_ndvi(ndvi):
    classes = np.zeros_like(ndvi)
    classes = np.where((ndvi <= -0.1), 1, classes)
    classes = np.where((ndvi > -0.1) & (ndvi <= 0), 2, classes)
    classes = np.where((ndvi > 0) & (ndvi <= 0.2), 3, classes)
    classes = np.where((ndvi > 0.2) & (ndvi <= 0.4), 4, classes)
    classes = np.where((ndvi > 0.4) & (ndvi <= 0.6), 5, classes)
    classes = np.where((ndvi > 0.6) & (ndvi <= 0.8), 6, classes)
    classes = np.where((ndvi > 0.8), 7, classes)
    return classes.astype(int)

# Temporal Series by 30m Pixel
def temporal_series_by_pixel(ndvi_series):
    dates = sorted(ndvi_series.keys())
    pixel_means = []

    for date in dates:
        mean_value = np.mean(ndvi_series[date])
        pixel_means.append(mean_value)

    # Série Temporelle
    plt.figure(figsize=(14, 8))
    plt.plot(dates, pixel_means, marker='o', linestyle='-', color='blue')
    plt.xlabel('Dates')
    plt.ylabel('NDVI Moyen')
    plt.title('Évolution Temporelle du NDVI Moyen par Taille de Pixel de 30m')
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(ndvi_output_dir, "temporal_series_by_pixel.png"))
    plt.close()

    # Area Plot
    df_pixel = pd.DataFrame({'Date': dates, 'NDVI_Moyen': pixel_means})
    df_pixel.set_index('Date', inplace=True)
    df_pixel.plot.area(stacked=True, figsize=(14, 8), alpha=0.5)
    plt.title('NDVI Moyen par Taille de Pixel de 30m (Area Plot)')
    plt.xlabel('Dates')
    plt.ylabel('NDVI Moyen')
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(ndvi_output_dir, "area_plot_by_pixel.png"))
    plt.close()

    print("Séries temporelles par pixel sauvegardées avec succès.")

# Temporal Series by Vegetation Type
def temporal_series_by_vegetation(ndvi_series):
    dates = sorted(ndvi_series.keys())
    class_means = {label: [] for label in ndvi_labels}
    
    for date in dates:
        classified = classify_ndvi(ndvi_series[date])
        for i, label in enumerate(ndvi_labels):
            class_mean = np.mean(ndvi_series[date][classified == i + 1])
            class_means[label].append(class_mean)
    
    # Série Temporelle
    plt.figure(figsize=(14, 8))
    for label, values in class_means.items():
        plt.plot(dates, values, label=label)
    plt.xlabel('Dates')
    plt.ylabel('NDVI Moyen')
    plt.title('Évolution Temporelle du NDVI Moyen par Type de Végétation')
    plt.legend()
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(ndvi_output_dir, "temporal_series_by_vegetation.png"))
    plt.close()

    # Area Plot
    df_veg = pd.DataFrame(class_means, index=dates)
    df_veg.plot.area(stacked=True, figsize=(14, 8), alpha=0.5)
    plt.title('NDVI Moyen par Type de Végétation (Area Plot)')
    plt.xlabel('Dates')
    plt.ylabel('NDVI Moyen')
    plt.grid(True)
    plt.legend(loc='upper left')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(ndvi_output_dir, "area_plot_by_vegetation.png"))
    plt.close()

    print("Séries temporelles par type de végétation sauvegardées avec succès.")

# Main Function
if __name__ == "__main__":
    ndvi_series = load_ndvi_images()
    temporal_series_by_pixel(ndvi_series)
    temporal_series_by_vegetation(ndvi_series)
    print("Analyse complète terminée.")
