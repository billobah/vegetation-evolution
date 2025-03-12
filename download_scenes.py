from api import M2M
import logging

logging.basicConfig(level=logging.INFO,format='%(asctime)s - %(levelname)s - %(message)s')

params = {
    "datasetName": "landsat_tm_c2_l1",
    "collectionName": "LT05_L1TP_016037_20010723_20161128_01_T1",
    "spatialFilter": {
        "filterType": "mbr",
        "lowerLeft": {"latitude": 8.5, "longitude": -9.5},
        "upperRight": {"latitude": 9.8, "longitude": -8.2}
    },
    "temporalFilter": {
        "startDate": "2001-01-01",
        "endDate": "2001-12-31"
    },
    "maxResults": 3,
    "cloudCoverFilter": {"max": 10, "min": 0},
}

m2m = M2M()

scenes = m2m.searchScenes(**params)
downloadMeta = m2m.retrieveScenes(params['datasetName'],scenes)
