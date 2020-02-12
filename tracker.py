#!/usr/bin/env python3.7
"""MIUI Updates Tracker - By XiaomiFirmwareUpdater"""

import re
from datetime import datetime
from glob import glob
from os import remove, rename, path, environ, system

import yaml
from requests import post

import ao
import fastboot
import recovery_a as recovery
from discordbot import DiscordBot
from utils import is_roll_back, get_branch, get_region, get_type

# vars
GIT_OAUTH_TOKEN = environ['XFU']
BOT_TOKEN = environ['tg_bot_token']
DISCORD_BOT_TOKEN = environ['DISCORD_BOT_TOKEN']
CHANGES = []
CHANGED = []

RSS_HEAD = '<?xml version="1.0" encoding="utf-8"?>\n<rss version="2.0">\n<channel>\n' \
           '<title>MIUI Updates Tracker by XiaomiFirmwareUpdater</title>\n' \
           '<link>https://xiaomifirmwareupdater.com</link>\n' \
           '<description>A script that automatically tracks MIUI ROM releases!</description>'
RSS_TAIL = '</channel>\n</rss>'

with open('telegram.yml', 'r') as telegram_data:
    TELEGRAM = yaml.load(telegram_data, Loader=yaml.CLoader)


def load_devices():
    """
    load devices lists
    """
    with open('devices/names.yml', 'r') as names_:
        names = yaml.load(names_, Loader=yaml.CLoader)
    with open('devices/sr.yml', 'r') as stable_recovery:
        sr_devices = yaml.load(stable_recovery, Loader=yaml.CLoader)
    with open('devices/sf.yml', 'r') as stable_fastboot:
        sf_devices = yaml.load(stable_fastboot, Loader=yaml.CLoader)
    with open('devices/wr.yml', 'r') as weekly_recovery:
        wr_devices = yaml.load(weekly_recovery, Loader=yaml.CLoader)
    with open('devices/wf.yml', 'r') as weekly_fastboot:
        wf_devices = yaml.load(weekly_fastboot, Loader=yaml.CLoader)
    return names, sr_devices, sf_devices, wr_devices, wf_devices


def tg_post(message: str, chat: str) -> int:
    """
    post message to telegram
    """
    params = (
        ('chat_id', chat),
        ('text', message),
        ('parse_mode', "Markdown"),
        ('disable_web_page_preview', "yes")
    )
    telegram_url = "https://api.telegram.org/bot" + BOT_TOKEN + "/sendMessage"
    telegram_req = post(telegram_url, params=params)
    telegram_status = telegram_req.status_code
    if telegram_status == 200:
        pass
    elif telegram_status == 400:
        print("Bad recipient / Wrong text format")
    elif telegram_status == 401:
        print("Wrong / Unauthorized token")
    else:
        print("Unknown error")
        print("Response: " + telegram_req.reason)
    return telegram_status


def git_commit_push():
    """
    git add - git commit - git push
=    """
    today = str(datetime.today()).split('.')[0]
    system("git add *_recovery/*.yml *_fastboot/*.yml rss/ archive/ && "
           "git -c \"user.name=XiaomiFirmwareUpdater\" -c "
           "\"user.email=xiaomifirmwareupdater@gmail.com\" "
           "commit -m \"sync: {}\" && "" \
           ""git push -q https://{}@github.com/XiaomiFirmwareUpdater/"
           "miui-updates-tracker.git HEAD:master"
           .format(today, GIT_OAUTH_TOKEN))


def diff(name: str):
    """
    compare yaml files
    """
    try:
        with open(f'{name}/{name}.yml', 'r') as new,\
                open(f'{name}/old_{name}', 'r') as old_data:
            latest = yaml.load(new, Loader=yaml.CLoader)
            old = yaml.load(old_data, Loader=yaml.CLoader)
            first_run = False
    except FileNotFoundError:
        print(f"Can't find old {name} files, skipping")
        first_run = True
    if first_run is False:
        if len(latest) == len(old):
            changes = [new_ for new_, old_ in zip(latest, old)
                       if not new_['version'] == old_['version']]
            if changes:
                CHANGES.append(changes)
                CHANGED.append([f'{name}/{i["codename"]}.yml' for i in changes])
        else:
            old_codenames = [i["codename"] for i in old]
            new_codenames = [i["codename"] for i in latest]
            changes = [i for i in new_codenames if i not in old_codenames]
            if changes:
                CHANGES.append([i for i in latest for codename in changes
                                if codename == i["codename"]])
            CHANGED.append([f'{name}/{i}.yml' for i in changes])


def merge_yaml(name: str):
    """
    merge all devices yaml files into one file
    """
    print("Creating YAML files")
    yaml_files = [x for x in sorted(glob(f'{name}/*.yml')) if not x.endswith('recovery.yml')
                  and not x.endswith('fastboot.yml')]
    yaml_data = []
    for file in yaml_files:
        with open(file, "r") as yaml_file:
            yaml_data.append(yaml.load(yaml_file, Loader=yaml.CLoader))
    with open(f'{name}/{name}', "w") as output:
        yaml.dump(yaml_data, output, Dumper=yaml.CDumper)
    if path.exists(f'{name}/{name}'):
        rename(f'{name}/{name}', f'{name}/{name}.yml')


def generate_message(update: dict):
    """
    generates telegram message
    """
    android = update['android']
    codename = update['codename']
    device = update['device']
    download = update['download']
    filename = update['filename']
    filesize = update['size']
    version = update['version']
    branch = get_branch(version).capitalize()
    region = get_region(filename, codename, version)
    rom_type = get_type(filename)
    codename = codename.split('_')[0]
    message = f"New {branch} {rom_type} update available!\n"
    message += f"*Device:* {device} \n" \
        f"*Codename:* #{codename} \n" \
        f"*Region:* {region} \n" \
        f"*Version:* `{version}` \n" \
        f"*Android:* {android} \n" \
        f"*Size*: {filesize} \n" \
        f"*Download*: [Here]({download})\n\n" \
        f"[Latest Updates](https://xiaomifirmwareupdater.com/miui/{codename}) - " \
               f"[All Updates](https://xiaomifirmwareupdater.com/archive/miui/{codename})\n" \
        "@MIUIUpdatesTracker | @XiaomiFirmwareUpdater"
    return message


def post_message(message: str):
    """
    post the generated message
    """
    codename = message.splitlines()[2].split('#')[1].strip()
    to_post = ["@MIUIUpdatesTracker"]
    if codename in TELEGRAM.keys():
        for i in TELEGRAM[codename]:
            to_post.append(i)
    for chat in to_post:
        status = tg_post(message, chat)
        if status == 200:
            print(f"{codename}: Telegram Message sent to {chat}")


def generate_rss(files: list):
    """
    generate RSS feed
    """
    def write_rss(update: dict):
        device = update['device']
        download = update['download']
        version = update['version']
        message = generate_message(update)
        message = message.replace('*', '').replace('[Here](', '')\
            .replace(')', '').replace('#', '').replace('`', '')
        message = "\n".join(message.splitlines()[:-2])
        message = "".join([f'<p>{i}</p>\n' for i in message.splitlines()])
        message += f'<a href="{download}">Download</a>'
        rss_body = f'<item>\n' \
            f'<title>MIUI {version} update for {device}</title>\n' \
            f'<link>{download}</link>\n' \
            f'<pubDate>{str(datetime.today()).split(".")[0]}</pubDate>\n' \
            f'<description><![CDATA[{message}]]></description>\n' \
            f'</item>'
        return rss_body

    rss = ''
    for branch in files:
        for file in branch:
            with open(file, "r") as yaml_file:
                info = yaml.load(yaml_file, Loader=yaml.CLoader)
            if isinstance(info, dict):
                rss = f'{RSS_HEAD}\n{write_rss(info)}\n{RSS_TAIL}'
            elif isinstance(info, list):
                rss = f'{RSS_HEAD}\n'
                for item in info:
                    rss += f'{write_rss(item)}\n'
                rss += f'{RSS_TAIL}'
            with open(f'rss/{file.split(".")[0]}.xml', 'w', newline='\n') as rss_file:
                rss_file.write(rss)


def merge_rss(name: str):
    """
    merge all devices rss xml files into one file
    """
    xml_files = [x for x in sorted(glob(f'rss/{name}/*.xml')) if not x.endswith('recovery.xml')
                 and not x.endswith('fastboot.xml')]
    xml_items = []
    for file in xml_files:
        with open(file, "r") as xml_file:
            xml = xml_file.read()
        try:
            item = re.findall(r'<item>(?:[\s\S]*?)</item>', xml, re.MULTILINE)[0]
        except IndexError:
            continue
        xml_items.append(item)
    with open(f'rss/{name}/{name}.xml', 'w', newline='\n') as out:
        out.write(f'{RSS_HEAD}\n')
        for item in xml_items:
            out.write(f'{item}\n')
        out.write(f'{RSS_TAIL}')


def archive(update: dict):
    """Append new update to the archive"""
    codename = update['codename']
    link = update['download']
    version = update['version']
    branch = get_branch(version)
    rom_type = 'recovery' if update['filename'].endswith('.zip') else 'fastboot'
    try:
        with open(f'archive/{branch}_{rom_type}/{codename}.yml', 'r') as yaml_file:
            data = yaml.load(yaml_file, Loader=yaml.CLoader)
            data[codename].update({version: link})
            data.update({codename: data[codename]})
            with open(f'archive/{branch}_{rom_type}/{codename}.yml', 'w') as output:
                yaml.dump(data, output, Dumper=yaml.CDumper)
    except FileNotFoundError:
        data = {codename: {version: link}}
        with open(f'archive/{branch}_{rom_type}/{codename}.yml', 'w') as output:
            yaml.dump(data, output, Dumper=yaml.CDumper)


def merge_archive():
    """
    merge all archive yaml files into one file
    """
    print("Creating archive YAML files")
    for name in ['stable_recovery', 'stable_fastboot', 'weekly_recovery', 'weekly_fastboot']:
        yaml_files = [x for x in sorted(glob(f'archive/{name}/*.yml'))
                      if not x.endswith('recovery.yml')
                      and not x.endswith('fastboot.yml')]
        yaml_data = []
        for file in yaml_files:
            with open(file, "r") as yaml_file:
                yaml_data.append(yaml.load(yaml_file, Loader=yaml.CLoader))
        with open(f'archive/{name}/{name}', "w") as output:
            yaml.dump(yaml_data, output, Dumper=yaml.CDumper)
        if path.exists(f'archive/{name}/{name}'):
            rename(f'archive/{name}/{name}', f'archive/{name}/{name}.yml')


def main():
    """
    MIUI Updates Tracker
    """
    names, sr_devices, sf_devices, wr_devices, wf_devices = load_devices()
    fastboot_roms = {'stable_fastboot': {'branch': 'F', 'devices': sf_devices}}
    recovery_roms = {'stable_recovery': {'branch': '1', 'devices': sr_devices}}
    ao_run = False
    discord_bot = DiscordBot(DISCORD_BOT_TOKEN)
    for name, data in fastboot_roms.items():
        # fetch based on version
        rename(f'{name}/{name}.yml', f'{name}/old_{name}')
        fastboot.fetch(data['devices'], data['branch'], name, names)
        print(f"Fetched {name}")
        if "stable_fastboot" in name and ao_run is False:
            ao.main()
            ao_run = True
        # Merge files
        merge_yaml(name)
        # Compare
        print(f"Comparing {name} files")
        diff(name)
    for name, data in recovery_roms.items():
        rename(f'{name}/{name}.yml', f'{name}/old_{name}')
        recovery.get_roms(data['devices'], data['branch'], name, names)
        print(f"Fetched {name}")
        merge_yaml(name)
        print(f"Comparing {name} files")
        diff(name)
    if CHANGES:
        generate_rss(CHANGED)
        updates = [x for y in CHANGES for x in y]
        for update in updates:
            if is_roll_back(update):
                continue
            message = generate_message(update)
            # print(message)
            post_message(message)
            archive(update)
        discord_bot.send(updates)
    else:
        print('No new updates found!')
    versions = [i for i in fastboot_roms.keys()] + [i for i in recovery_roms.keys()]
    for version in versions:
        merge_rss(version)
    merge_archive()
    print("Done")
    git_commit_push()
    for file in glob(f'*_*/old_*'):
        remove(file)


if __name__ == '__main__':
    main()
