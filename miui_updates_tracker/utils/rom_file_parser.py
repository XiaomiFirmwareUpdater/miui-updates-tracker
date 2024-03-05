import logging
import re
from datetime import datetime

from requests import head
from requests.exceptions import ConnectionError as RequestsConnectionError

logger = logging.getLogger(__name__)


def get_headers(link):
    """Perform a HEAD request safely"""
    headers = None
    try:
        headers = head(link.replace('bigota.d.miui.com', 'cdn-ota.azureedge.net')).headers
    except RequestsConnectionError as err:
        logger.error(f"ConnectionError when trying to get headers of {link}\n{err}")
    return headers


def rom_info_from_file(rom_file: str, more_details: bool = False):
    """Parse recovery rom zip file and return its information"""
    pattern = re.compile(
        r'miui_([\w\d]+)_(.*)_([a-z0-9]+)_([0-9.]+)\.zip')
    match = pattern.search(rom_file)
    link = f"https://cdn-ota.azureedge.net/{match.group(2)}/{rom_file}"
    miui_name = match.group(1).replace('PRE', '') \
        if match.group(1).endswith('PRE') and not match.group(2).startswith('V') \
        else match.group(1)
    info = {'miui_name': miui_name,
            'version': match.group(2),
            'md5_part': match.group(3),
            'android': match.group(4),
            'filename': rom_file,
            'link': link}
    if more_details:
        headers = get_headers(link)
        if headers:
            try:
                date = datetime.strptime(' '.join(headers['Last-Modified'].split(', ')[1].split(' ')[:3]),
                                         '%d %b %Y').strftime("%Y-%m-%d")
            except KeyError:
                date = None
            info.update({'date': date, 'size': headers['Content-Length']})
    return info


def ota_info_from_file(ota_file: str, more_details: bool = False):
    """Parse incremental rom zip file and return its information"""
    pattern = re.compile(
        r'miui-(?:block)?ota-([a-z0-9_]+)-(.*)-(.*)-([a-z0-9]+)-([0-9.]+)\.zip')
    match = pattern.search(ota_file)
    link = f"https://cdn-ota.azureedge.net/{match.group(3)}/{ota_file}"
    info = {'codename': match.group(1),
            'version_from': match.group(2),
            'version': match.group(3),
            'md5_part': match.group(4),
            'android': match.group(5),
            'filename': ota_file,
            'link': link}
    if more_details:
        headers = get_headers(link)
        if headers:
            date = None
            try:
                date = datetime.strptime(' '.join(headers['Last-Modified'].split(', ')[1].split(' ')[:3]),
                                         '%d %b %Y').strftime("%Y-%m-%d")
            except KeyError as err:
                print(err, headers)
            info.update({'date': date, 'size': headers['Content-Length']})
    return info


def fastboot_info_from_file(fastboot_file: str, more_details: bool = False):
    """Parse fastboot rom zip file and return its information"""
    pattern = re.compile(
        r'([\d\w_]+)_images_(V\.?\d{1,2}\.\d{,2}\.\d{,2}\.\d{,2}\.\d{,2}?\.?[A-Z]{3,}'
        r'|\d{,2}\.\d{,2}\.\d{,2})_(?:\.1_)?(\d{8})?(?:\.0000)?(?:\.\d{,2})?'
        r'_([0-9.]+)_?([a-z]+)?_(?:\w+_)?([a-z0-9]+)\.tgz')
    alt_pattern = re.compile(r'([\d\w_]+)_images_(.*)_(\d{8})?(?:\.0000\.\d{,2})?'
                             r'_?([0-9.]+)_([a-z]+)_([a-z0-9]+)\.tgz')
    match = pattern.search(fastboot_file)
    if match:
        version = match.group(2)
    else:
        match = alt_pattern.search(fastboot_file)
        version = match.group(2)
        if ".debug" in version:
            version = version.split(".debug")[0]
        if '_' in version:
            version = version.split('_')[0]
    link = f"https://cdn-ota.azureedge.net/{version}/{fastboot_file}"
    info = {'codename': match.group(1),
            'version': version,
            'android': match.group(4),
            'region': match.group(5),
            'md5_part': match.group(6),
            'filename': fastboot_file,
            'link': link}
    if more_details:
        headers = get_headers(link)
        if headers:
            try:
                date = datetime.strptime(match.group(3), '%Y%m%d').strftime("%Y-%m-%d") if match.group(
                    3) else datetime.strptime(' '.join(headers['Last-Modified'].split(', ')[1].split(' ')[:3]),
                                              '%d %b %Y').strftime("%Y-%m-%d")
            except KeyError:
                date = None
            info.update({'date': date, 'size': headers['Content-Length']})
    return info
