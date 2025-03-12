from api import M2M
import logging

logging.basicConfig(level=logging.INFO,format='%(asctime)s - %(levelname)s - %(message)s')

params = {
    "datasetName": "landsat_tm_c2_l1",
    "spatialFilter": {
        "filterType": "mbr",
        "lowerLeft": {"latitude": 8.5, "longitude": -9.5},
        "upperRight": {"latitude": 9.8, "longitude": -8.2}
    },
    "temporalFilter": {
        "startDate": "2001-01-01",
        "endDate": "2001-12-31"
    },
    "maxResults": 1,
    "cloudCoverFilter": {"max": 10, "min": 0},
}

m2m = M2M()

scenes = m2m.searchScenes(**params)
downloadMeta = m2m.retrieveScenes(params['datasetName'],scenes)
