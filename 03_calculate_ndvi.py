# Import Libraries
import os
import numpy as np
import matplotlib.pyplot as plt
import rasterio
from glob import glob


# Folders Configuration

cropped_dir = 'data/raw/cropped_straightened'
ndvi_output_dir = 'ndvi/ndvi_cropped_straightened_images'
os.makedirs(ndvi_output_dir, exist_ok=True)


# Crop to Same Size
def crop_to_same_size(image1, image2):
    min_rows = min(image1.shape[0], image2.shape[0])
    min_cols = min(image1.shape[1], image2.shape[1])
    
    image1_cropped = image1[:min_rows, :min_cols]
    image2_cropped = image2[:min_rows, :min_cols]
    
    return image1_cropped, image2_cropped


# NDVI Calculation
def calculate_ndvi(red, nir):
    ndvi = np.where((nir + red) == 0., 0, (nir - red) / (nir + red))
    return ndvi

def calculate_and_save_ndvi(red, nir, date_str):
    ndvi = calculate_ndvi(red, nir)
    save_path = os.path.join(ndvi_output_dir, f"{date_str}_ndvi.png")
    plt.figure(figsize=(10, 8))
    plt.imshow(ndvi, cmap='RdYlGn', vmin=-1, vmax=1)
    plt.colorbar(label='NDVI Value')
    plt.title(f'NDVI Map - {date_str}')
    plt.savefig(save_path)
    plt.close()
    print(f"NDVI Image saved: {save_path}")
    return ndvi


# Load Images
def load_band(image_path):
    with rasterio.open(image_path) as src:
        image = src.read(1).astype('float32')
    return image


# Process Images
def process_images():
    ndvi_series = {}
    
    # Loop through date directories in cropped_straightened
    for date_dir in sorted(glob(os.path.join(cropped_dir, '*'))):
        date_str = os.path.basename(date_dir)
        print(f"\nProcessing images for date: {date_str}")
        
        # Find B3 (Red) and B4 (NIR) files
        b3_files = glob(os.path.join(date_dir, '*_B3_Rouge_cropped_straightened.TIF'))
        b4_files = glob(os.path.join(date_dir, '*_B4_NIR_cropped_straightened.TIF'))
        
        if not b3_files or not b4_files:
            print(f"No B3 or B4 images found for date: {date_str}")
            continue
        
        # Load B3 (Red) and B4 (NIR) images
        b3_path = b3_files[0]
        b4_path = b4_files[0]
        red = load_band(b3_path)
        nir = load_band(b4_path)
        
        # Crop to the same size
        red_cropped, nir_cropped = crop_to_same_size(red, nir)
        
        # Calculate and save NDVI
        ndvi = calculate_and_save_ndvi(red_cropped, nir_cropped, date_str)
        ndvi_series[date_str] = ndvi
        
    return ndvi_series


# Main Function
if __name__ == "__main__":
    ndvi_series = process_images()
    print("\nNDVI calculation completed.")
