import concurrent.futures
import logging
import time
import subprocess
import requests
import random
import os
import os.path as osp

from six.moves.urllib import request as urequest

sleep_seconds = 5
total_max_retries = 3
wget = 'wget'
wget_options = ["--quiet", "--read-timeout=1", "--random-wait", "--progress=dot:giga", "--limit-rate=10m"]
download_sleep_seconds = 3

max_threads = 10

class DownloadError(Exception):
    """Raised when the downloader is unable to retrieve a URL."""
    pass

def download_url(url, local_path, max_retries=total_max_retries, sleep_seconds=sleep_seconds):
    """Download a remote URL to the location local_path with retries."""
    dname = osp.basename(local_path)
    logging.info(f'download_url - {dname} - downloading {url} as {local_path}')
    sec = random.random() * download_sleep_seconds
    time.sleep(sec)

    try:
        r = requests.get(url, stream=True)
        content_size = int(r.headers.get('content-length', 0))
        if content_size == 0:
            logging.error('download_url - content size is 0')
            raise DownloadError('Content size is 0')
    except Exception as e:
        if max_retries > 0:
            logging.info(f'download_url - {dname} - retrying ({max_retries} retries left)')
            time.sleep(sleep_seconds)
            return download_url(url, local_path, max_retries=max_retries-1, sleep_seconds=sleep_seconds)
        logging.error(f'download_url - {dname} - no more retries available')
        raise DownloadError(f'Failed to find file {url}')

    remove(local_path)
    logging.info(f'download_url - {dname} - starting download...')

    with open(ensure_dir(local_path), 'wb') as f:
        f.write(r.raw.read())

    file_size = osp.getsize(local_path)
    if int(file_size) != int(content_size) and content_size > 0:
        logging.warning(f'download_url - {dname} - wrong file size, retrying, {max_retries} retries left')
        if max_retries > 0:
            time.sleep(sleep_seconds)
            return download_url(url, local_path, max_retries=max_retries-1, sleep_seconds=sleep_seconds)
        remove(local_path)
        raise DownloadError(f'Failed to download file {url}')

    info_path = local_path + '.size'
    with open(ensure_dir(info_path), 'w') as f:
        f.write(str(content_size))

    logging.info(f'download_url - {dname} - success download')

def download_scenes(downloads, downloadMeta, download_dir=None):
    """Download all scenes using multithreading."""
    logging.info(f'download_scenes - downloading {len(downloads)} scenes')

    # If no download_dir specified, use default
    if download_dir is None:
        download_dir = '../data/raw/landsat'

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_threads) as executor:
        futures = []
        for download in downloads:
            url = download['url']
            idD = str(download['downloadId'])
            if idD in downloadMeta.keys():
                displayId = downloadMeta[idD]['displayId']
                local_path = osp.join(download_dir, displayId + '.tar')
                if available_locally(local_path):
                    logging.info(f'downloadScenes - file {local_path} is already available')
                else:
                    future = executor.submit(download_url, url, local_path)
                    futures.append(future)
                downloadMeta[idD].update({'url': url, 'local_path': local_path})
            else:
                logging.warning(f'download_scenes - scene ID {idD} not found in metadata')

        finished = 0
        for future in concurrent.futures.as_completed(futures):
            finished += 1
            logging.info(f'download_scenes - {finished}/{len(futures)} downloads finished')

    logging.info('download_scenes - all downloads finished')

def ensure_dir(path):
    """Ensure all directories in path exist. Return path itself."""
    path_dir = osp.dirname(path)
    if not osp.exists(path_dir):
        os.makedirs(path_dir)
    return path

def remove(tgt):
    """Remove a file if it exists."""
    if osp.isfile(tgt):
        logging.info(f'remove - removing file {tgt}')
        os.remove(tgt)

def available_locally(path):
    """Check if a file is available locally and correct."""
    info_path = path + '.size'
    if osp.exists(path) and osp.exists(info_path):
        content_size = int(open(info_path).read())
        return osp.getsize(path) == content_size and content_size > 0
    return False
