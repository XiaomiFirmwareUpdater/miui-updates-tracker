#!/usr/bin/env python3.7
"""Xiaomi MIUI EOL devices ROMs fetcher"""

import json
from glob import glob
from os import remove, rename, path

import fastboot
import recovery

# load devices lists
with open('names.json', 'r') as n:
    NAMES = json.load(n)
with open('sr.json', 'r') as sr:
    SR_DEVICES = json.load(sr)
with open('sf.json', 'r') as sf:
    SF_DEVICES = json.load(sf)
with open('wr.json', 'r') as wr:
    WR_DEVICES = json.load(wr)
with open('wf.json', 'r') as wf:
    WF_DEVICES = json.load(wf)
VERSIONS = ['stable_recovery', 'stable_fastboot', 'weekly_recovery', 'weekly_fastboot']

for v in VERSIONS:
    folder = v + '/'
    # backup old
    if path.exists(v + '/' + v + '.json'):
        rename(v + '/' + v + '.json', v + '/' + 'old_' + v)
    # set branches and devices
    devices = ''
    branch = ''
    if "stable_recovery" in v:
        branch = "1"
        devices = SR_DEVICES
    elif "stable_fastboot" in v:
        branch = "F"
        devices = SF_DEVICES
    elif "weekly_recovery" in v:
        branch = "0"
        devices = WR_DEVICES
    elif "weekly_fastboot" in v:
        branch = "X"
        devices = WF_DEVICES
    # fetch based on version
    if "_recovery" in v:
        recovery.fetch(devices, branch, folder, NAMES)
    elif "_fastboot" in v:
        fastboot.fetch(devices, branch, folder, NAMES)
    print("Fetched " + v.replace('_', ' '))

    # Merge files
    print("Creating JSON")
    json_files = [x for x in sorted(glob(v + '/' + '*.json'))]
    json_data = list()
    for file in json_files:
        with open(file, "r") as f:
            json_data.append(json.load(f))
    with open(v + '/' + v, "w") as f:
        json.dump(json_data, f, indent=1)

    # Cleanup
    for file in glob(v + '/' + '*.json'):
        remove(file)
    if path.exists(v + '/' + v):
        rename(v + '/' + v, v + '/' + v + '.json')
