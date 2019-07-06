#!/usr/bin/env python3.7
"""MIUI Updates Tracker - By XiaomiFirmwareUpdater"""

import json
import re
from datetime import datetime
from glob import glob
from os import remove, rename, path, environ, system, makedirs
from requests import post
import fastboot
import recovery_a as recovery
import ao

# vars
GIT_OAUTH_TOKEN = environ['XFU']
BOT_TOKEN = environ['bottoken']
TG_CHAT = "@MIUIUpdatesTracker"
DISCORD_BOT_TOKEN = environ['DISCORD_BOT_TOKEN']
CHANNEL_ID = "484478392562089995"
CHANGES = []
CHANGED = []

RSS_HEAD = '<?xml version="1.0" encoding="utf-8"?>\n<rss version="2.0">\n<channel>\n' \
           '<title>MIUI Updates Tracker by XiaomiFirmwareUpdater</title>\n' \
           '<link>https://xiaomifirmwareupdater.com</link>\n' \
           '<description>A script that automatically tracks MIUI ROM releases!</description>'
RSS_TAIL = '</channel>\n</rss>'


def initialize():
    """
    creates required folders and copy old files
    """
    makedirs("stable_recovery", exist_ok=True)
    makedirs("stable_fastboot", exist_ok=True)
    makedirs("weekly_recovery", exist_ok=True)
    makedirs("weekly_fastboot", exist_ok=True)
    for file in glob('*_*/*.json'):
        full_name = file.split('/')[-1]
        if 'old_' in file:
            continue
        if 'recovery' in full_name or 'fastboot' in full_name:
            name = 'old_' + full_name.split('.')[0]
            rename(file, '/'.join(file.split('/')[:-1]) + '/' + name)


def load_devices():
    """
    load devices lists
    """
    with open('devices/names.json', 'r') as names_:
        names = json.load(names_)
    with open('devices/sr.json', 'r') as stable_recovery:
        sr_devices = json.load(stable_recovery)
    with open('devices/sf.json', 'r') as stable_fastboot:
        sf_devices = json.load(stable_fastboot)
    with open('devices/wr.json', 'r') as weekly_recovery:
        wr_devices = json.load(weekly_recovery)
    with open('devices/wf.json', 'r') as weekly_fastboot:
        wf_devices = json.load(weekly_fastboot)
    return names, sr_devices, sf_devices, wr_devices, wf_devices


def tg_post(message: str):
    """
    post message to telegram
    """
    params = (
        ('chat_id', TG_CHAT),
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


def discord_post(message: str):
    """
    post message to discord
    """
    discord_url = "https://discordapp.com/api/channels/{}/messages".format(CHANNEL_ID)
    headers = {"Authorization": "Bot {}".format(DISCORD_BOT_TOKEN),
               "User-Agent": "myBotThing (http://some.url, v0.1)",
               "Content-Type": "application/json", }
    data = json.dumps({"content": message})
    discord_req = post(discord_url, headers=headers, data=data)
    discord_status = discord_req.status_code
    if discord_status == 200:
        pass
    else:
        print("Discord Error")
    return discord_status


def git_commit_push():
    """
    git add - git commit - git push
=    """
    today = str(datetime.today()).split('.')[0]
    system("git add *_recovery/*.json *_fastboot/*.json rss/ && "
           "git -c \"user.name=XiaomiFirmwareUpdater\" -c "
           "\"user.email=xiaomifirmwareupdater@gmail.com\" "
           "commit -m \"sync: {}\" && "" \
           ""git push -q https://{}@github.com/XiaomiFirmwareUpdater/"
           "miui-updates-tracker.git HEAD:master"
           .format(today, GIT_OAUTH_TOKEN))


def diff(name: str):
    """
    compare json files
    """
    try:
        with open(f'{name}/{name}.json', 'r') as new,\
                open(f'{name}/old_{name}', 'r') as old_data:
            latest = json.load(new)
            old = json.load(old_data)
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
                CHANGED.append([f'{name}/{i["codename"]}.json' for i in changes])
        else:
            old_codenames = [i["codename"] for i in old]
            new_codenames = [i["codename"] for i in latest]
            changes = [i for i in new_codenames if i not in old_codenames]
            if changes:
                CHANGES.append([i for i in latest for codename in changes
                                if codename == i["codename"]])
            CHANGED.append([f'{name}/{i["codename"]}.json' for i in changes])


def merge_json(name: str):
    """
    merge all devices json files into one file
    """
    print("Creating JSON files")
    json_files = [x for x in sorted(glob(f'{name}/*.json')) if not x.endswith('recovery.json')
                  and not x.endswith('fastboot.json')]
    json_data = []
    for file in json_files:
        with open(file, "r") as json_file:
            json_data.append(json.load(json_file))
    with open(f'{name}/{name}', "w") as output:
        json.dump(json_data, output, indent=1)


def generate_message(update: dict):
    """
    generates telegram message
    """
    android = update['android']
    codename = update['codename']
    device = update['device']
    download = update['download']
    filename = update['filename']
    version = update['version']
    if 'V' in version:
        branch = 'Stable'
    else:
        branch = 'Weekly'
    if 'eea_global' in filename or 'eea_global' in codename or 'EU' in version:
        region = 'EEA Global'
    elif 'in_global' in filename or 'in_global' in codename or 'IN' in version:
        region = 'India'
    elif 'ru_global' in filename or 'ru_global' in codename or 'RU' in version:
        region = 'Russia'
    elif 'global' in filename or 'global' in codename or 'MI' in version:
        region = 'Global'
    else:
        region = 'China'
    if '.tgz' in filename:
        rom_type = 'Fastboot'
    else:
        rom_type = 'Recovery'
    codename = codename.split('_')[0]
    message = f"New {branch} {rom_type} update available!\n"
    message += f"*Device:* {device} \n" \
        f"*Codename:* #{codename} \n" \
        f"*Region:* {region} \n" \
        f"*Version:* `{version}` \n" \
        f"*Android:* {android} \n" \
        f"*Download*: [Here]({download}) \n" \
        "@MIUIUpdatesTracker | @XiaomiFirmwareUpdater"
    return message


def post_message(message: str):
    """
    post the generated message
    """
    codename = message.splitlines()[2].split('#')[1].strip()
    status = tg_post(message)
    if status == 200:
        print(f"{codename}: Telegram Message sent")
    discord_separator = '~~                                                     ~~'
    discord_message = message.replace('*', '**')\
        .replace('@MIUIUpdatesTracker | @XiaomiFirmwareUpdater', discord_separator)\
        .replace('[Here](', '').replace(')', '')
    status = discord_post(discord_message)
    if status == 200:
        print(f"{codename}: Discord Message sent")


def generate_rss(files: list):
    """
    generate RSS feed
    """
    def write_rss(update: dict):
        device = update['device']
        download = update['download']
        version = update['version']
        message = generate_message(update)
        message = message.replace('*', '').replace('[Here](', '').replace(')', '').replace('#', '')\
            .replace('http', '<a>http').replace('.tgz', '.tgz</a>').replace('.zip', '.zip</a>')
        message = "".join([f'<p>{i}</p>\n' for i in message.splitlines()])
        rss_body = f'<item>\n' \
            f'<title>MIUI {version} update for {device}</title>\n' \
            f'<link>{download}</link>\n' \
            f'<pubDate>{str(datetime.today()).split(".")[0]}</pubDate>\n' \
            f'<description><![CDATA[{message}]]></description>\n' \
            f'</item>'
        return rss_body

    rss = ''
    for file in files:
        file = file[0]
        with open(file, "r") as json_file:
            info = json.load(json_file)
        if isinstance(info, dict):
            rss = f'{RSS_HEAD}\n{write_rss(info)}\n{RSS_TAIL}'
        elif isinstance(info, list):
            rss = f'{RSS_HEAD}\n'
            for item in info:
                rss += f'{write_rss(item)}\n'
            rss += f'{RSS_TAIL}'
        with open(f'rss/{file.split(".")[0]}.xml', 'w') as rss_file:
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
    with open(f'rss/{name}/{name}.xml', 'w') as out:
        out.write(f'{RSS_HEAD}\n')
        for item in xml_items:
            out.write(f'{item}\n')
        out.write(f'{RSS_TAIL}')


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
    ao_run = False
    for name, data in versions.items():
        # fetch based on version
        if "_fastboot" in name:
            fastboot.fetch(data['devices'], data['branch'], f'{name}/', names)
        elif "_recovery" in name:
            recovery.get_roms(name)
        print("Fetched " + name.replace('_', ' '))
        if "stable_fastboot" in name and ao_run is False:
            ao.main()
            ao_run = True
        # Merge files
        merge_json(name)
        if path.exists(f'{name}/{name}'):
            rename(f'{name}/{name}', f'{name}/{name}.json')
        # Compare
        print("Comparing")
        diff(name)
        print("Done")
    if CHANGES:
        generate_rss(CHANGED)
        for update in CHANGES:
            message = generate_message(update[0])
            post_message(message)
    else:
        print('No new updates found!')
    for version in versions.keys():
        merge_rss(version)
    git_commit_push()
    for file in glob(f'*_*/old_*'):
        remove(file)


if __name__ == '__main__':
    main()
