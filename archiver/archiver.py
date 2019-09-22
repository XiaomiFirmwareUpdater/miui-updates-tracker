#!/usr/bin/env python3.7
"""MIUI Updates Tracker channel dumper"""

from collections import OrderedDict
from glob import glob
import yaml
from bs4 import BeautifulSoup
from requests import get

with open("../devices/names.yml", 'r') as f:
    DEVICES = yaml.load(f, Loader=yaml.CLoader)

CODES = yaml.load(get('https://raw.githubusercontent.com/XiaomiFirmwareUpdater/'
                      'xiaomi_devices/miui_codes/miui.yml').text, Loader=yaml.CLoader)


def fetch_links():
    """Read html and text files and extract links"""
    stable_recovery = []
    stable_fastboot = []
    weekly_recovery = []
    weekly_fastboot = []

    def filter_roms(links_list):
        for link in links_list:
            if '.zip' in str(link) and link.split('/')[3].startswith('V'):
                stable_recovery.append(link)
            if '.tgz' in str(link) and link.split('/')[3].startswith('V'):
                stable_fastboot.append(link)
            if '.zip' in str(link) and not link.split('/')[3].startswith('V'):
                weekly_recovery.append(link)
            if '.tgz' in str(link) and not link.split('/')[3].startswith('V'):
                weekly_fastboot.append(link)

    for file in glob('*.html'):
        with open(file, "r") as html_file:
            html = html_file.read()
        page = BeautifulSoup(html, 'html.parser')
        all_links = sorted(list(set(link['href'] for link in page.findAll("a"))))
        filter_roms(all_links)
    with open('links.txt', 'r') as txt:
        links = txt.read().strip().splitlines()
    filter_roms(links)
    # remove duplicates and sort
    stable_recovery = sorted(list(set(stable_recovery)))
    stable_fastboot = sorted(list(set(stable_fastboot)))
    weekly_recovery = sorted(list(set(weekly_recovery)))
    weekly_fastboot = sorted(list(set(weekly_fastboot)))

    return stable_recovery, stable_fastboot, weekly_recovery, weekly_fastboot


def gen_yaml(links, folder):
    """
    generate yaml file with device's info for each rom link
    :param links: a list of links
    :param folder: stable/weekly
    """
    if 'fastboot' in folder:
        codenames = sorted(list(set(link.split('/')[-1].split('_images')[0] for link in links)))
    else:
        devices = sorted(list(set(link.split('/')[-1].split('_')[1] for link in links)))
        codenames = []
        for model in devices:
            try:
                for codename, info in DEVICES.items():
                    if info[1] == model:
                        codenames.append(codename)
            except IndexError as err:
                print(f"can't find codename for {model}\n{err}")
                continue
    for codename in codenames:
        data = {}
        roms = []
        if 'fastboot' in folder:
            roms = [link for link in links if codename == link.split('/')[-1].split('_images')[0]]
        elif 'stable_recovery' in folder:
            try:
                roms = [link for link in links if CODES[codename] in link.split('/')[3]]
            # except KeyError as e:
            # print(f'KeyError {e}')
            except KeyError:
                continue
        elif 'weekly_recovery' in folder:
            if codename == 'whyred_global':
                roms = [link for link in links
                        if link.split('/')[-1].split('_')[1].startswith(DEVICES[codename][1])
                        or link.split('/')[-1].split('_')[1] == 'HMNote5Global']
            else:
                roms = [link for link in links
                        if link.split('/')[-1].split('_')[1] == DEVICES[codename][1]]
        info = {}
        for rom in roms:
            if 'fastboot' in folder:
                version = rom.split('/')[3]
            else:
                version = rom.split('/')[-1].split('_')[2]
            info.update({version: rom})
        info = OrderedDict(sorted(info.items(), reverse=True))
        data.update({codename: info})
        with open(f'{folder}/{codename}.yml', 'w') as output:
            yaml.dump(data, output, Dumper=yaml.CDumper)


def main():
    """MIUIUpdatesTracker archiver"""
    stable_recovery, stable_fastboot, weekly_recovery, weekly_fastboot = fetch_links()
    gen_yaml(stable_recovery, 'stable_recovery')
    gen_yaml(stable_fastboot, 'stable_fastboot')
    gen_yaml(weekly_recovery, 'weekly_recovery')
    gen_yaml(weekly_fastboot, 'weekly_fastboot')


if __name__ == '__main__':
    main()
