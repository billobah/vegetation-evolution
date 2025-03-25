from utils import telechargement_scenes
from utils import extraction_images
from utils import crop_straighten_images
from ndvi import compute_ndvi
from ndvi import analyze_ndvi


if __name__ == "__main__":
    telechargement_scenes.main()
    extraction_images.main()
    crop_straighten_images.main()
    compute_ndvi.main()
    analyze_ndvi.main()
