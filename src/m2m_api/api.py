import logging
import requests
import json
import random
import time
import os.path as osp
from pathlib import Path
from getpass import getpass

from src.m2m_api.filters import Filter
from src.m2m_api.downloader import download_scenes

M2M_ENDPOINT = 'https://m2m.cr.usgs.gov/api/api/json/{}/'
logging.getLogger('requests').setLevel(logging.WARNING)

class M2MError(Exception):
    """Raised when an M2M gets an error."""
    pass

class M2M(object):
    """M2M EarthExplorer API."""

    def __init__(self, username=None, password=None, token=None, version="stable"):
        self.serviceUrl = M2M_ENDPOINT.format(version)
        self.apiKey = None
        self.authenticate(username, password, token)
        allDatasets = self.sendRequest('dataset-search')
        self.datasetNames = [dataset['datasetAlias'] for dataset in allDatasets]
        self.permissions = self.sendRequest('permissions')

    def authenticate(self, username, password, token):
        config_path = Path(osp.expandvars('~/.config/m2m_api')).expanduser().resolve()
        config_file = config_path / 'config.json'

        try:
            config = json.load(open(config_file))
        except:
            config_path.mkdir(parents=True, exist_ok=True)
            config = {}

        self.username = username or config.get('username')
        if self.username is None:
            self.username = input("Enter your username (or email): ")
            config['username'] = self.username

        if password:
            self.login(password)
        elif token:
            config.update({'username': self.username, 'token': token})
            json.dump(config, open(config_file, 'w'), indent=4, separators=(',', ': '))
            self.loginToken(token)
        else:
            token = config.get('token')
            if token is None:
                option = input("Use password (p) or token (t)? ").lower()
                if option == "p":
                    self.login(getpass())
                else:
                    token = input('Enter your token: ')
                    config.update({'username': self.username, 'token': token})
                    json.dump(config, open(config_file, 'w'), indent=4, separators=(',', ': '))
                    self.loginToken(token)
            else:
                self.loginToken(token)

    def sendRequest(self, endpoint, data={}, max_retries=5):
        url = osp.join(self.serviceUrl, endpoint)
        logging.info(f'sendRequest - url = {url}')
        json_data = json.dumps(data)
        headers = {'X-Auth-Token': self.apiKey} if self.apiKey else {}

        response = retry_connect(url, json_data, headers=headers, max_retries=max_retries)
        if response is None:
            raise M2MError("No output from service")

        status = response.status_code
        try:
            output = json.loads(response.text)
        except Exception:
            output = response.text

        if status != 200 or (isinstance(output, dict) and output.get('errorCode')):
            msg = f"{status} - {output.get('errorCode', '')} - {output.get('errorMessage', '')}" if isinstance(output, dict) else f"{status} - {output}"
            raise M2MError(msg)

        response.close()
        return output['data']

    def login(self, password=None):
        if password is None:
            raise M2MError('Password not provided')
        loginParameters = {'username': self.username, 'password': password}
        self.apiKey = self.sendRequest('login', loginParameters)

    def loginToken(self, token=None):
        if token is None:
            raise M2MError('Token not provided')
        loginParameters = {'username': self.username, 'token': token}
        self.apiKey = self.sendRequest('login-token', loginParameters)

    def searchDatasets(self, **args):
        args['processList'] = ['datasetName', 'acquisitionFilter', 'spatialFilter']
        params = Filter(args)
        return self.sendRequest('dataset-search', params)

    def datasetFilters(self, **args):
        args['processList'] = ['datasetName']
        params = Filter(args)
        return self.sendRequest('dataset-filters', params)

    def searchScenes(self, datasetName, **args):
        if datasetName not in self.datasetNames:
            raise M2MError(f"Dataset {datasetName} not one of the available datasets {self.datasetNames}")
        args['datasetName'] = datasetName
        if 'metadataInfo' in args and len(args['metadataInfo']):
            args['datasetFilters'] = self.datasetFilters(**args)
        args['processList'] = ['datasetName', 'sceneFilter', 'maxResults']
        params = Filter(args)
        scenes = self.sendRequest('scene-search', params)
        if scenes['totalHits'] > scenes['recordsReturned']:
            logging.warning(f'M2M.searchScenes - more hits {scenes["totalHits"]} than returned records {scenes["recordsReturned"]}')
        return scenes

    def sceneListAdd(self, listId, datasetName, **args):
        if datasetName not in self.datasetNames:
            raise M2MError(f"Dataset {datasetName} not one of the available datasets {self.datasetNames}")
        args.update({'listId': listId, 'datasetName': datasetName})
        self.sendRequest('scene-list-add', args)

    def sceneListGet(self, listId, **args):
        args['listId'] = listId
        self.sendRequest('scene-list-get', args)

    def sceneListRemove(self, listId, **args):
        args['listId'] = listId
        self.sendRequest('scene-list-remove', args)

    def downloadOptions(self, datasetName, filterOptions={}, **args):
        if datasetName not in self.datasetNames:
            raise M2MError(f"Dataset {datasetName} not one of the available datasets {self.datasetNames}")
        args['datasetName'] = datasetName
        downloadOptions = self.sendRequest('download-options', args)
        return apply_filter(downloadOptions, filterOptions)

    def downloadRequest(self, downloadList, label='m2m-api_download'):
        params = {'downloads': downloadList, 'label': label}
        return self.sendRequest('download-request', params)

    def downloadRetrieve(self, label='m2m-api_download'):
        params = {'label': label}
        return self.sendRequest('download-retrieve', params)

    def downloadSearch(self, label=None):
        params = {'label': label} if label else {}
        return self.sendRequest('download-search', params)

    def downloadOrderRemove(self, label):
        params = {'label': label}
        self.sendRequest('download-order-remove', params)

    def retrieveScenes(self, datasetName, scenes, filterOptions={}, label='m2m-api_download', download_dir=None):
        """Méthode corrigée pour accepter un chemin de téléchargement dynamique."""
        entityIds = [scene['entityId'] for scene in scenes['results']]
        self.sceneListAdd(label, datasetName, entityIds=entityIds)
        downloadMeta = {}
        if not filterOptions:
            filterOptions = {'downloadSystem': lambda x: x in ['dds', 'ls_zip'], 'available': lambda x: x}

        labels = [label]
        downloadOptions = self.downloadOptions(datasetName, filterOptions, listId=label, includeSecondaryFileGroups=False)
        downloads = [{'entityId': product['entityId'], 'productId': product['id']} for product in downloadOptions]

        requestedDownloadsCount = len(downloads)
        if requestedDownloadsCount:
            logging.info(f'M2M.retrieveScenes - Requested downloads count={requestedDownloadsCount}')
            requestResults = self.downloadRequest(downloads, label=label)

            if requestResults.get('duplicateProducts'):
                for product in requestResults['duplicateProducts'].values():
                    if product not in labels:
                        labels.append(product)

            for lbl in labels:
                downloadSearch = self.downloadSearch(lbl)
                if downloadSearch:
                    for ds in downloadSearch:
                        downloadMeta[str(ds['downloadId'])] = ds

            if requestResults.get('preparingDownloads'):
                downloadIds = []
                for lbl in labels:
                    requestResultsUpdated = self.downloadRetrieve(lbl)
                    downloadUpdate = requestResultsUpdated['available'] + requestResultsUpdated['requested']
                    download_scenes(downloadUpdate, downloadMeta, download_dir=download_dir)
                    downloadIds += downloadMeta

                while len(downloadIds) < requestedDownloadsCount:
                    preparingDownloads = requestedDownloadsCount - len(downloadIds)
                    logging.info(f'M2M.retrieveScenes - {preparingDownloads} downloads are not available. Waiting 10 seconds...')
                    time.sleep(10)
                    for lbl in labels:
                        requestResultsUpdated = self.downloadRetrieve(lbl)
                        downloadUpdate = requestResultsUpdated['available']
                        download_scenes(downloadUpdate, downloadMeta, download_dir=download_dir)
                        downloadIds += downloadUpdate
            else:
                download_scenes(requestResults['availableDownloads'], downloadMeta, download_dir=download_dir)
        else:
            logging.info('M2M.retrieveScenes - No download options found')

        for lbl in labels:
            self.downloadOrderRemove(lbl)
            self.sceneListRemove(lbl)

        return downloadMeta

    def logout(self):
        if self.sendRequest('logout') is not None:
            raise M2MError("Not able to logout")
        self.apiKey = None

    def __exit__(self, exc_type, exc_value, traceback):
        self.logout()

def retry_connect(url, json_data, headers={}, max_retries=5, sleep_seconds=2, timeout=600):
    retries = 0
    while retries < max_retries:
        try:
            response = requests.post(url, json_data, headers=headers, timeout=timeout)
            return response
        except requests.exceptions.Timeout:
            retries += 1
            logging.info(f'Connection Timeout - retry {retries} of {max_retries}')
            time.sleep(random.random() * sleep_seconds + 1.0)
    raise M2MError("Maximum retries exceeded")

def apply_filter(elements, key_filters):
    result = []
    if elements is not None:
        for element in elements:
            if all(filt(element[key]) for key, filt in key_filters.items()):
                result.append(element)
    return result
