import logging
import re
from datetime import datetime

from requests import head
from requests.exceptions import ConnectionError as RequestsConnectionError

logger = logging.getLogger(__name__)

cdn = 'bkt-sgp-miui-ota-update-alisgp.oss-ap-southeast-1.aliyuncs.com'
cdn_url = f'https://{cdn}'
miui_zip_pattern = re.compile(
    r'miui_(?P<miui_name>[\w\d]+)_(?P<version>.*)_(?P<md5_part>[\w\d]+)_(?P<android>[\d.]+)\.zip'
)
miui_incremental_pattern = re.compile(
    r'miui-(?:block)?ota-(?P<codename>[\w\d_]+)-(?P<version_from>.*)-(?P<version>.*)-(?P<md5_part>[\w\d]+)-(?P<android>[\d.]+)\.zip'
)
hos2_zip_pattern = re.compile(
    r'(?P<codename>[\w\d_]+)-ota_full-(?P<version>[\da-zA-Z.]+)-(?P<type>\w+)-(?P<android>[\d.]+)-(?P<md5_part>[\w\d]+)\.zip'
)
hos2_incremental_pattern = re.compile(
    r'(?P<codename>[\w\d_]+)-ota_incremental-(?P<version_from>[\da-zA-Z.]+)-(?P<version>[\da-zA-Z.]+)-(?P<type>\w+)-(?P<android>[\d.]+)-(?P<md5_part>[\w\d]+)\.zip'
)


def get_headers(link):
    """Perform a HEAD request safely"""
    headers = None
    try:
        headers = head(link.replace('bigota.d.miui.com', cdn)).headers
    except RequestsConnectionError as err:
        logger.error(f'ConnectionError when trying to get headers of {link}\n{err}')
    return headers


def rom_info_from_file(rom_file: str, more_details: bool = False):
    """Parse recovery rom zip file and return its information"""
    match = miui_zip_pattern.search(rom_file) or hos2_zip_pattern.search(rom_file)
    groups = match.groupdict()
    link = f'{cdn_url}/{groups.get("version")}/{rom_file}'
    miui_name = groups.get('miui_name')
    if (
        groups.get('miui_name')
        and miui_name.endswith('PRE')
        and not groups.get('version').startswith('V')
    ):
        miui_name = miui_name.replace('PRE', '')
    info = {
        'miui_name': miui_name,
        'version': groups.get('version'),
        'md5_part': groups.get('md5_part'),
        'android': groups.get('android'),
        'filename': rom_file,
        'link': link,
    }
    if groups.get('codename'):
        info.update({'codename': groups.get('codename')})
    if more_details:
        headers = get_headers(link)
        if headers:
            try:
                date = datetime.strptime(
                    ' '.join(headers['Last-Modified'].split(', ')[1].split(' ')[:3]),
                    '%d %b %Y',
                ).strftime('%Y-%m-%d')
            except KeyError:
                date = None
            info.update({'date': date, 'size': headers['Content-Length']})
    return info


def ota_info_from_file(ota_file: str, more_details: bool = False):
    """Parse incremental rom zip file and return its information"""
    match = miui_incremental_pattern.search(ota_file) or hos2_incremental_pattern.search(ota_file)
    groups = match.groupdict()
    link = f'{cdn_url}/{groups.get(3)}/{ota_file}'
    info = {
        'codename': groups.get('codename'),
        'version_from': groups.get('version_from'),
        'version': groups.get('version'),
        'md5_part': groups.get('md5_part'),
        'android': groups.get('android'),
        'filename': ota_file,
        'link': link,
    }
    if more_details:
        headers = get_headers(link)
        if headers:
            date = None
            try:
                date = datetime.strptime(
                    ' '.join(headers['Last-Modified'].split(', ')[1].split(' ')[:3]),
                    '%d %b %Y',
                ).strftime('%Y-%m-%d')
            except KeyError as err:
                print(err, headers)
            info.update({'date': date, 'size': headers['Content-Length']})
    return info


def fastboot_info_from_file(fastboot_file: str, more_details: bool = False):
    """Parse fastboot rom zip file and return its information"""
    pattern = re.compile(
        r'([\d\w_]+)_images_([VOS]+\.?\d{1,}\.\d{,2}\.\d{,2}\.\d{,2}\.\d{,2}?\.?[A-Z]{3,}'
        r'|\d{,2}\.\d{,2}\.\d{,2})_(?:\.1_)?(\d{8})?(?:\.0000)?(?:\.\d{,2})?'
        r'_([0-9.]+)_?([a-z]+)?_(?:\w+_)?([a-z0-9]+)\.tgz'
    )
    alt_pattern = re.compile(
        r'([\d\w_]+)_images_(.*)_(\d{8})?(?:\.0000\.\d{,2})?'
        r'_?([0-9.]+)_([a-z]+)_([a-z0-9]+)\.tgz'
    )
    match = pattern.search(fastboot_file)
    if match:
        version = match.group(2)
    else:
        match = alt_pattern.search(fastboot_file)
        version = match.group(2)
        if '.debug' in version:
            version = version.split('.debug')[0]
        if '_' in version:
            version = version.split('_')[0]
    link = f'{cdn_url}/{version}/{fastboot_file}'
    info = {
        'codename': match.group(1),
        'version': version,
        'android': match.group(4),
        'region': match.group(5),
        'md5_part': match.group(6),
        'filename': fastboot_file,
        'link': link,
    }
    if more_details:
        headers = get_headers(link)
        if headers:
            try:
                date = (
                    datetime.strptime(match.group(3), '%Y%m%d').strftime('%Y-%m-%d')
                    if match.group(3)
                    else datetime.strptime(
                        ' '.join(headers['Last-Modified'].split(', ')[1].split(' ')[:3]),
                        '%d %b %Y',
                    ).strftime('%Y-%m-%d')
                )
            except KeyError:
                date = None
            info.update({'date': date, 'size': headers['Content-Length']})
    return info
