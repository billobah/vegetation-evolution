# Import Libraries
import os
import cv2
import rasterio
from glob import glob
import numpy as np

# Define input and output directories
input_dir = '../data/raw/landsat'
cropped_dir = '../data/cropped_straightened'
os.makedirs(cropped_dir, exist_ok=True)

# Loading images
def load_band(band_path):
    with rasterio.open(band_path) as src:
        band = src.read(1).astype('float32')
        band_meta = src.meta
    return band, band_meta

# Order the corners of the rectangle
def order_points(pts):
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    return rect

# Detect contour and straighten the image
def detect_and_straighten(image, meta, date_str, band_name):
    norm_image = cv2.normalize(image, None, 0, 255, cv2.NORM_MINMAX).astype('uint8')
    _, thresholded = cv2.threshold(norm_image, 1, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresholded, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if not contours:
        print("Aucun contour trouvé.")
        return image
    
    largest_contour = max(contours, key=cv2.contourArea)
    epsilon = 0.02 * cv2.arcLength(largest_contour, True)
    approx = cv2.approxPolyDP(largest_contour, epsilon, True)
    
    if len(approx) >= 4:
        pts = approx.reshape(-1, 2)
        rect = order_points(pts)
        
        (tl, tr, br, bl) = rect
        maxWidth = int(max(np.linalg.norm(br - bl), np.linalg.norm(tr - tl)))
        maxHeight = int(max(np.linalg.norm(tr - br), np.linalg.norm(tl - bl)))
        
        dst = np.array([
            [0, 0],
            [maxWidth - 1, 0],
            [maxWidth - 1, maxHeight - 1],
            [0, maxHeight - 1]
        ], dtype="float32")
        
        M = cv2.getPerspectiveTransform(rect, dst)
        straightened_image = cv2.warpPerspective(image, M, (maxWidth, maxHeight))
        
        # Sauvegarde de l'image redressée au format TIF
        save_path = os.path.join(cropped_dir, f"{date_str}_{band_name}_cropped_straightened.TIF")
        meta.update({
            "height": straightened_image.shape[0],
            "width": straightened_image.shape[1]
        })
        
        with rasterio.open(save_path, 'w', **meta) as dst:
            dst.write(straightened_image, 1)
        
        print(f"Image redressée et sauvegardée : {save_path}")
        return straightened_image
    else:
        print("Les coins n'ont pas été correctement détectés.")
        return image

# Process each image in the directory
def process_images():
    for date_dir in sorted(glob(os.path.join(input_dir, '*'))):
        date_str = os.path.basename(date_dir)
        
        # Rechercher les fichiers B3 et B4
        b3_files = glob(os.path.join(date_dir, '*_B3.TIF'))
        b4_files = glob(os.path.join(date_dir, '*_B4.TIF'))
        
        if not b3_files or not b4_files:
            print(f"Pas de fichiers B3 ou B4 trouvés pour la date : {date_str}")
            continue
        
        # Charger les images B3 et B4
        b3_path = b3_files[0]
        b4_path = b4_files[0]
        red, red_meta = load_band(b3_path)
        nir, nir_meta = load_band(b4_path)
        
        # Découper et redresser les images
        detect_and_straighten(red, red_meta, date_str, 'B3_Rouge')
        detect_and_straighten(nir, nir_meta, date_str, 'B4_NIR')

# Main Function
if __name__ == "__main__":
    process_images()
    print("Découpage et redressement des images terminés.")
