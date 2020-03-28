#!/usr/bin/env python3.7
"""Xiaomi MIUI Stable fastboot script for android one devices"""

import json
import yaml
from bs4 import BeautifulSoup
from requests import get
from humanize import naturalsize

DEVICES = {"daisy_global": {"name": "Mi A2 Lite", "model": "daisy", "id": "1700354"},
           "jasmine_global": {"name": "Mi A2", "model": "jasmine", "id": "1700353"},
           "laurel_sprout_global": {"name": "Mi A3", "model": "laurel", "id": "1900372"},
           "tiare_eea_global": {"name": "Redmi Go EEA", "model": "tiare", "id": "1700365"},
           "tiare_global": {"name": "Redmi Go Global", "model": "tiare", "id": "1700365"},
           "tiare_in_global": {"name": "Redmi Go India", "model": "tiare", "id": "1700365"},
           "tiare_ru_global": {"name": "Redmi Go Russia", "model": "tiare", "id": "1700365"},
           "tissot": {"name": "Mi A1", "model": "tissot", "id": "1700333"}
           }
DATA = []


def get_fastboot(codename, info):
    """    fetch MIUI ROMs downloads"""
    headers = {
        'Pragma': 'no-cache',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Referer': f'http://c.mi.com/oc/miuidownload/detail?device={info["id"]}',
        'X-Requested-With': 'XMLHttpRequest',
        'Connection': 'keep-alive',
        'Cache-Control': 'no-cache',
    }
    try:
        data = list(get(
            f"https://c.mi.com/oc/rom/getdevicelist?phone_id={info['id']}",
            headers=headers).json()['data']['device_data']['device_list'].values())
    except AttributeError:
        return
    try:
        for device in data:
            if device['stable_rom']['rom_url']:
                link = device['stable_rom']['rom_url'].strip()
                if codename in link:
                    # print(link)
                    add_rom(codename, link, info)
    except KeyError:
        try:
            for device in data:
                if device['developer_rom']['rom_url']:
                    link = device['developer_rom']['rom_url'].strip()
                    if codename in link:
                        add_rom(codename, link, info)
        except KeyError:
            pass


def add_rom(codename, link, info):
    update = {}
    file_size = naturalsize(int(get(link, stream=True).headers['Content-Length']))
    file = link.split('/')[-1]
    version = link.split('/')[3]
    android = link.split('_')[-2]
    update.update({"android": android})
    update.update({"codename": codename})
    update.update({"device": info['name']})
    update.update({"download": link})
    update.update({"filename": file})
    update.update({"size": file_size})
    update.update({"md5": "null"})
    update.update({"version": version})
    DATA.append(update)
    with open(f'stable_fastboot/{codename}.yml', 'w', newline='\n') as output:
        yaml.dump(update, output, Dumper=yaml.CDumper)


def main():
    """loop through MIUI downloads and get the link"""
    for codename, info in DEVICES.items():
        get_fastboot(codename, info)
    # write all json to one file
    # with open('ao.json', 'w', newline='\n') as ao:
    #     json.dump(DATA, ao, indent=1)


if __name__ == '__main__':
    main()
