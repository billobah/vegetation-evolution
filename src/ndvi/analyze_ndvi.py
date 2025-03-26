# Import Libraries
import os
import numpy as np
import matplotlib.pyplot as plt
import rasterio
from glob import glob
import pandas as pd
from fpdf import FPDF

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

color_palette = [
    "#1f77b4", "#ff7f0e", "#2ca02c",
    "#d62728", "#9467bd", "#8c564b", "#e377c2"
]

# Load NDVI Images
def load_ndvi_images():
    ndvi_series = {}
    for file in sorted(glob(os.path.join(ndvi_input_dir, '*_ndvi.png'))):
        date_str = os.path.basename(file).split('_ndvi.png')[0]
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

# NDVI Temporal Evolution by Pixel
def temporal_series_by_pixel(ndvi_series):
    dates = sorted(ndvi_series.keys())
    pixel_means = [np.mean(ndvi_series[date]) for date in dates]

    # Plot
    plt.figure(figsize=(14, 8))
    plt.plot(dates, pixel_means, marker='o', linestyle='-', color='blue')
    plt.xlabel('Dates')
    plt.ylabel('NDVI Moyen')
    plt.title('Évolution Temporelle du NDVI Moyen par Taille de Pixel de 30m')
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()
    path_plot = os.path.join(ndvi_output_dir, "temporal_series_by_pixel.png")
    plt.savefig(path_plot)
    plt.close()

    # CSV + Area Plot
    df_pixel = pd.DataFrame({'Date': dates, 'NDVI_Moyen': pixel_means})
    df_pixel.set_index('Date', inplace=True)
    df_pixel.to_csv(os.path.join(ndvi_output_dir, "ndvi_moyen_par_pixel.csv"))

    df_pixel.plot.area(stacked=False, figsize=(14, 8), alpha=0.5)
    plt.title('NDVI Moyen par Taille de Pixel de 30m (Area Plot)')
    plt.xlabel('Dates')
    plt.ylabel('NDVI Moyen')
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()
    area_path = os.path.join(ndvi_output_dir, "area_plot_by_pixel.png")
    plt.savefig(area_path)
    plt.close()

    return path_plot, area_path

# NDVI Temporal Evolution by Vegetation Class
def temporal_series_by_vegetation(ndvi_series):
    dates = sorted(ndvi_series.keys())
    class_means = {label: [] for label in ndvi_labels}

    for date in dates:
        classified = classify_ndvi(ndvi_series[date])
        for i, label in enumerate(ndvi_labels):
            mask = (classified == i + 1)
            class_means[label].append(np.mean(ndvi_series[date][mask]) if np.any(mask) else 0)

    # Line plot
    plt.figure(figsize=(14, 8))
    for i, (label, values) in enumerate(class_means.items()):
        plt.plot(dates, values, label=label, color=color_palette[i])
    plt.xlabel('Dates')
    plt.ylabel('NDVI Moyen')
    plt.title('Évolution Temporelle du NDVI Moyen par Type de Végétation')
    plt.legend()
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plot_path = os.path.join(ndvi_output_dir, "temporal_series_by_vegetation.png")
    plt.savefig(plot_path)
    plt.close()

    # CSV + Area plot
    df_veg = pd.DataFrame(class_means, index=dates)
    df_veg.to_csv(os.path.join(ndvi_output_dir, "ndvi_moyen_par_vegetation.csv"))

    df_veg.plot.area(stacked=False, figsize=(14, 8), alpha=0.5, color=color_palette)
    plt.title('NDVI Moyen par Type de Végétation (Area Plot)')
    plt.xlabel('Dates')
    plt.ylabel('NDVI Moyen')
    plt.grid(True)
    plt.legend(loc='upper left')
    plt.xticks(rotation=45)
    plt.tight_layout()
    area_path = os.path.join(ndvi_output_dir, "area_plot_by_vegetation.png")
    plt.savefig(area_path)
    plt.close()

    return plot_path, area_path

# Générer un rapport PDF avec les graphiques NDVI
def generate_pdf_report(image_paths, output_path):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)

    pdf.add_page()
    pdf.set_font("Arial", size=16)
    pdf.cell(200, 10, txt="Rapport NDVI - Analyse Temporelle", ln=True, align='C')
    pdf.set_font("Arial", size=12)
    pdf.ln(10)

    for img_path in image_paths:
        if os.path.exists(img_path):
            pdf.image(img_path, w=180)
            pdf.ln(10)
        else:
            pdf.cell(200, 10, f"[Fichier manquant] {img_path}", ln=True, align='L')

    pdf.output(output_path)
    print(f"📄 Rapport PDF généré : {output_path}")

# Main Function
def main(ndvi_series):
    print("Début analyse NDVI")

    if not ndvi_series or not isinstance(ndvi_series, dict):
        print("ERREUR : Aucun NDVI transmis ou format incorrect.")
        return

    pixel_plot, pixel_area = temporal_series_by_pixel(ndvi_series)
    veg_plot, veg_area = temporal_series_by_vegetation(ndvi_series)

    report_path = os.path.join(ndvi_output_dir, "rapport_ndvi.pdf")
    generate_pdf_report([pixel_plot, pixel_area, veg_plot, veg_area], report_path)

    print("Analyse NDVI terminée.")