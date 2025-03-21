import logging
import requests
import json
import random
import time
import os.path as osp
from pathlib import Path
from getpass import getpass

from filters import Filter
from downloader import download_scenes

M2M_ENDPOINT = 'https://m2m.cr.usgs.gov/api/api/json/{}/'
logging.getLogger('requests').setLevel(logging.WARNING)

class M2MError(Exception):
    """
    Raised when an M2M gets an error.
    """
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
        config_path = '~/.config/m2m_api'
        config_path = Path(osp.expandvars(config_path)).expanduser().resolve()
        config_file = config_path / 'config.json'
        try:
            config = json.load(open(config_file))
        except:
            config_path.mkdir(parents=True, exist_ok=True)
            config = {} 
        
        self.username = username
        if self.username is None:
            self.username = config.get('username')
            if self.username is None:
                username = input("Enter your username (or email): ")
                self.username = username
                config['username'] = username
            
        if password != None:
            self.login(password)
        elif token != None:
            config = {
                'username': username,
                'token': token
            }
            json.dump(config, open(config_file, 'w'), indent=4, separators=(',', ': '))
            self.loginToken(token)
        else:
            token = config.get('token')
            if token is None:
                option = None
                while option not in ["p", "P", "t", "T"]:
                    option = input("Want to use password (p) or token (t)? ")
                if option in ["p", "P"]:
                    password = getpass()
                    self.login(password)
                else:
                    token = input('Enter your token: ')
                    config = {
                        'username': username,
                        'token': token
                    }
                    json.dump(config, open(config_file, 'w'), indent=4, separators=(',', ': '))
                    self.loginToken(token)
            else:
                self.loginToken(token)

    def sendRequest(self, endpoint, data={}, max_retries=5):
        url = osp.join(self.serviceUrl, endpoint)
        logging.info('sendRequest - url = {}'.format(url))
        json_data = json.dumps(data)
        if self.apiKey == None:
            response = retry_connect(url, json_data, max_retries=max_retries)
        else:
            headers = {'X-Auth-Token': self.apiKey}   
            response = retry_connect(url, json_data, headers=headers, max_retries=max_retries)
        if response == None:
            raise M2MError("No output from service")
        status = response.status_code 
        try:
            output = json.loads(response.text)
        except:
            output = response.text
        if status != 200:
            if isinstance(output,dict):
                msg = "{} - {} - {}".format(status,output['errorCode'],output['errorMessage'])
            else:
                msg = "{} - {}".format(status,output)
            raise M2MError(msg)
        else:
            if isinstance(output,dict): 
                if output['data'] is None and output['errorCode'] is not None and endpoint != 'logout':
                    msg = "{} - {}".format(output['errorCode'],output['errorMessage'])
                    raise M2MError(msg)
            else:
                msg = "{} - {}".format(status,output)
                raise M2MError(msg)
        response.close()
        return output['data']

    def login(self, password=None):
        if password is None:
            raise M2MError('password not provided')
        loginParameters = {'username': self.username, 'password': password}
        self.apiKey = self.sendRequest('login', loginParameters)

    def loginToken(self, token=None):
        if token is None: 
            raise M2MError('token not provided')
        loginParameters = {'username': self.username, 'token': token}
        self.apiKey = self.sendRequest('login-token', loginParameters)

    def searchDatasets(self, **args):
        args['processList'] = ['datasetName','acquisitionFilter','spatialFilter']
        params = Filter(args)
        return self.sendRequest('dataset-search', params)

    def datasetFilters(self, **args):
        args['processList'] = ['datasetName']
        params = Filter(args)
        return self.sendRequest('dataset-filters', params)

    def searchScenes(self, datasetName, **args):
        if datasetName not in self.datasetNames:
            raise M2MError("Dataset {} not one of the available datasets {}".format(datasetName,self.datasetNames))
        args['datasetName'] = datasetName
        if 'metadataInfo' in args and len(args['metadataInfo']):
            args['datasetFilters'] = self.datasetFilters(**args)
        args['processList'] = ['datasetName','sceneFilter','maxResults']
        params = Filter(args)
        scenes = self.sendRequest('scene-search', params)
        if scenes['totalHits'] > scenes['recordsReturned']:
            logging.warning('M2M.searchScenes - more hits {} than returned records {}, consider increasing maxResults parameter.'.format(scenes['totalHits'],
                                                                                                                                        scenes['recordsReturned']))
        return scenes

    def sceneListAdd(self, listId, datasetName, **args):
        args['listId'] = listId
        if datasetName not in self.datasetNames:
            raise M2MError("Dataset {} not one of the available datasets {}".format(datasetName,self.datasetNames))
        args['datasetName'] = datasetName
        self.sendRequest('scene-list-add', args)
    
    def sceneListGet(self, listId, **args):
        args['listId'] = listId
        self.sendRequest('scene-list-get', args)

    def sceneListRemove(self, listId, **args):
        args['listId'] = listId
        self.sendRequest('scene-list-remove', args)

    def downloadOptions(self, datasetName, filterOptions={}, **args):
        if datasetName not in self.datasetNames:
            raise M2MError("Dataset {} not one of the available datasets {}".format(datasetName,self.datasetNames))
        args['datasetName'] = datasetName
        downloadOptions = self.sendRequest('download-options', args)
        filteredOptions = apply_filter(downloadOptions, filterOptions)
        return filteredOptions
            
    def downloadRequest(self, downloadList, label='m2m-api_download'):
        params = {'downloads': downloadList,
                'label': label}
        return self.sendRequest('download-request', params)

    def downloadRetrieve(self, label='m2m-api_download'):
        params = {'label': label}
        return self.sendRequest('download-retrieve', params)

    def downloadSearch(self, label=None):
        if label is not None:
            params = {'label': label}
            return self.sendRequest('download-search', params)
        return self.sendRequest('download-search')

    def downloadOrderRemove(self, label):
        params = {'label': label}
        self.sendRequest('download-order-remove', params)

    def retrieveScenes(self, datasetName, scenes, filterOptions={}, label='m2m-api_download'):
        entityIds = [scene['entityId'] for scene in scenes['results']]
        self.sceneListAdd(label, datasetName, entityIds=entityIds)
        downloadMeta = {}
        if not len(filterOptions):
            filterOptions = {'downloadSystem': lambda x: x in ['dds', 'ls_zip'], 'available': lambda x: x}
        labels = [label]
        downloadOptions = self.downloadOptions(
            datasetName, filterOptions, listId=label, includeSecondaryFileGroups=False
        )
        downloads = [
            {
                'entityId' : product['entityId'], 'productId' : product['id']
            } for product in downloadOptions
        ]
        requestedDownloadsCount = len(downloads)
        if requestedDownloadsCount:
            logging.info('M2M.retrieveScenes - Requested downloads count={}'.format(requestedDownloadsCount))
            requestResults = self.downloadRequest(downloads, label=label)
            if len(requestResults['duplicateProducts']):
                for product in requestResults['duplicateProducts'].values():
                    if product not in labels:
                        labels.append(product)
            for label in labels:
                downloadSearch = self.downloadSearch(label)
                if downloadSearch is not None:
                    for ds in downloadSearch:
                        downloadMeta.update({str(ds['downloadId']): ds})
            if requestResults['preparingDownloads'] != None and len(requestResults['preparingDownloads']) > 0:
                downloadIds = []
                for label in labels:
                    requestResultsUpdated = self.downloadRetrieve(label)
                    downloadUpdate = requestResultsUpdated['available'] + requestResultsUpdated['requested']
                    download_scenes(downloadUpdate, downloadMeta)
                    downloadIds += downloadMeta
                while len(downloadIds) < requestedDownloadsCount:
                    preparingDownloads = requestedDownloadsCount - len(downloadIds)
                    logging.info('M2M.retrieveScenes - {} downloads are not available. Waiting 10 seconds...'.format(preparingDownloads))
                    time.sleep(10)
                    for label in labels:
                        requestResultsUpdated = self.downloadRetrieve(label)
                        downloadUpdate = requestResultsUpdated['available']
                        download_scenes(downloadUpdate, downloadMeta)
                        downloadIds += downloadUpdate
            else:
                download_scenes(requestResults['availableDownloads'], downloadMeta)
        else:
            logging.info('M2M.retrieveScenes - No download options found')
        for label in labels:
            self.downloadOrderRemove(label)
            self.sceneListRemove(label)
        return downloadMeta

    def logout(self):
        r = self.sendRequest('logout')
        if r != None:
            raise M2MError("Not able to logout")
        self.apiKey = None

    def __exit__(self):
        self.logout()

def retry_connect(url, json_data, headers={}, max_retries=5, sleep_seconds=2, timeout=600):
    retries = 0
    while retries < max_retries:
        try:
            response = requests.post(url, json_data, headers=headers, timeout=timeout)
            return response
        except requests.exceptions.Timeout:
            retries += 1
            logging.info('Connection Timeout - retry number {} of {}'.format(retries,max_retries))
            sec = random.random() * sleep_seconds + 100.
            time.sleep(sec)
    raise M2MError("Maximum retries exceeded")

def apply_filter(elements, key_filters):
    result = []
    if elements != None:
        for element in elements:
            get_elem = True
            for key,filt in key_filters.items():
                if not filt(element[key]):
                    get_elem = False
            if get_elem:
                result.append(element)
    return result
