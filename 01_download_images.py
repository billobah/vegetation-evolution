# Import Libraries
import os
import json
import tarfile
from dotenv import load_dotenv
from landsatxplore.api import API
from landsatxplore.earthexplorer import EarthExplorer

# Load environment variables from .env file for connection to LandsatXplore API
load_dotenv()

# Retrieve USGS IDs from environment variables
username = os.getenv('USGS_USERNAME')
password = os.getenv('USGS_PASSWORD')

# Initialize the LandsatXplore API
api = API(username, password)

# Search Landsat TM images (B3 and B4) for a given site
scenes = api.search(
    dataset='LANDSAT_TM_C2_L1',
    latitude=9.16,
    longitude=-9.16,
    start_date='1995-07-01',
    end_date='2020-09-01',
    max_cloud_cover=10
)

print(f"{len(scenes)} scènes trouvées.")

# Create output folder for downloads
output_dir = 'data/raw/landsat'
os.makedirs(output_dir, exist_ok=True)

# Initialize EarthExplorer for download
ee = EarthExplorer(username, password)

# Function to extract only bands B3 (RED) and B4 (NIR)
def extract_b3_b4(tar_path, dest_dir):
    """ Extraction des bandes B3 (Rouge) et B4 (NIR) depuis l'archive TAR """
    with tarfile.open(tar_path, 'r') as tar:
        members = tar.getmembers()
        # Filter to keep only files ending exactly with _B3.TIF or _B4.TIF
        b3_b4_members = [m for m in members if m.name.endswith('_B3.TIF') or m.name.endswith('_B4.TIF')]
        
        # If we find bands B3 and B4, we extract them
        if b3_b4_members:
            tar.extractall(path=dest_dir, members=b3_b4_members)
            print(f"Bandes B3 et B4 extraites dans : {dest_dir}")
        else:
            print(f"Pas de bandes B3 ou B4 trouvées dans : {tar_path}")

# Download and organize images by date
for scene in scenes:
    acquisition_date = scene['acquisition_date'].strftime('%Y-%m-%d')
    product_id = scene['landsat_product_id']
    print(f"\nTéléchargement de la scène : {product_id} pour la date : {acquisition_date}")
    
    # Create a folder by date
    date_dir = os.path.join(output_dir, acquisition_date)
    os.makedirs(date_dir, exist_ok=True)
    
    # Path to the TAR archive to download
    tar_path = os.path.join(date_dir, f"{product_id}.tar")
    
    # Download the image if it doesn't already exist
    if not os.path.exists(tar_path):
        try:
            ee.download(product_id, output_dir=date_dir)
            print(f"Téléchargement terminé : {tar_path}")
            
            # Extract only bands B3 and B4
            extract_b3_b4(tar_path, date_dir)
            
        except Exception as e:
            print(f"Erreur lors du téléchargement de la scène {product_id}: {e}")
    else:
        print(f"La scène {product_id} a déjà été téléchargée.")
        
# Disconnecting API and EarthExplorer
api.logout()
ee.logout()

print("\nTéléchargements terminés et images organisées par date.")