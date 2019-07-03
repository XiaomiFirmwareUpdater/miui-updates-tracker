#!/usr/bin/env python3.7
"""Xiaomi MIUI EOL devices ROMs fetcher"""

import json
from glob import glob
from os import remove, rename, path, makedirs
import fastboot
import recovery_a as recovery


def initialize():
    """
    creates required folders and copy old files
    """
    makedirs("stable_recovery", exist_ok=True)
    makedirs("stable_fastboot", exist_ok=True)
    makedirs("weekly_recovery", exist_ok=True)
    makedirs("weekly_fastboot", exist_ok=True)
    for file in glob('*_*/*.json'):
        if 'old_' in file:
            continue
        name = 'old_' + file.split('/')[-1].split('.')[0]
        rename(file, '/'.join(file.split('/')[:-1]) + '/' + name)


def load_devices():
    """
    load devices lists
    """
    with open('names.json', 'r') as names_:
        names = json.load(names_)
    with open('sr.json', 'r') as stable_recovery:
        sr_devices = json.load(stable_recovery)
    with open('sf.json', 'r') as stable_fastboot:
        sf_devices = json.load(stable_fastboot)
    with open('wr.json', 'r') as weekly_recovery:
        wr_devices = json.load(weekly_recovery)
    with open('wf.json', 'r') as weekly_fastboot:
        wf_devices = json.load(weekly_fastboot)
    return names, sr_devices, sf_devices, wr_devices, wf_devices


def main():
    """
    MIUI Updates Tracker
    """
    initialize()
    names, sr_devices, sf_devices, wr_devices, wf_devices = load_devices()
    versions = {'stable_fastboot': {'branch': 'F', 'devices': sf_devices},
                'stable_recovery': {'branch': '1', 'devices': sr_devices},
                'weekly_fastboot': {'branch': 'X', 'devices': wf_devices},
                'weekly_recovery': {'branch': '0', 'devices': wr_devices}}
    for name, data in versions.items():
        # fetch based on version
        if "_fastboot" in name:
            fastboot.fetch(data['devices'], data['branch'], f'{name}/', names)
        elif "_recovery" in name:
            recovery.get_roms(name)
        print("Fetched " + name.replace('_', ' '))
        # Merge files
        print("Creating JSON")
        json_files = [x for x in sorted(glob(f'{name}/*.json')) if not x.startswith('old_')]
        json_data = []
        for file in json_files:
            with open(file, "r") as json_file:
                json_data.append(json.load(json_file))
        with open(f'{name}/{name}', "w") as output:
            json.dump(json_data, output, indent=1)
        # Cleanup
        for file in glob(f'{name}/*.json'):
            remove(file)
        if path.exists(f'{name}/{name}'):
            rename(f'{name}/{name}', f'{name}/{name}.json')


if __name__ == '__main__':
    main()
