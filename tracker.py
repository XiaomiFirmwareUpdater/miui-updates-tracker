import difflib
import json
from datetime import datetime
from glob import glob
from os import remove, rename, path, environ, system
from requests import post
import fastboot
import recovery
import ao


def tg_post(message, codename_):
    params = (
        ('chat_id', telegram_chat),
        ('text', message),
        ('parse_mode', "Markdown"),
        ('disable_web_page_preview', "yes")
    )
    telegram_url = "https://api.telegram.org/bot" + bottoken + "/sendMessage"
    telegram_req = post(telegram_url, params=params)
    telegram_status = telegram_req.status_code
    if telegram_status == 200:
        print("{}: Telegram Message sent".format(codename_))
    else:
        print("Telegram Error")


def discord_post(message, codename_):
    discord_url = "https://discordapp.com/api/channels/{}/messages".format(channelID)
    headers = {"Authorization": "Bot {}".format(DISCORD_BOT_TOKEN),
               "User-Agent": "myBotThing (http://some.url, v0.1)",
               "Content-Type": "application/json", }
    data = json.dumps({"content": message})
    discord_req = post(discord_url, headers=headers, data=data)
    discord_status = discord_req.status_code
    if discord_status == 200:
        print("{0}: Discord Message sent".format(codename_))
    else:
        print("Discord Error")


# vars
GIT_OAUTH_TOKEN = environ['XFU']
bottoken = environ['bottoken']
telegram_chat = "@MIUIUpdatesTracker"
DISCORD_BOT_TOKEN = environ['DISCORD_BOT_TOKEN']
channelID = "484478392562089995"

# load devices lists
with open('devices/names.json', 'r') as n:
    names = json.load(n)
with open('devices/sr.json', 'r') as sr:
    sr_devices = json.load(sr)
with open('devices/sf.json', 'r') as sf:
    sf_devices = json.load(sf)
with open('devices/wr.json', 'r') as wr:
    wr_devices = json.load(wr)
with open('devices/wf.json', 'r') as wf:
    wf_devices = json.load(wf)
versions = ['stable_recovery', 'stable_fastboot', 'weekly_recovery', 'weekly_fastboot']

for v in versions:
    folder = v + '/'
    # backup old
    if path.exists(v + '/' + v + '.json'):
        rename(v + '/' + v + '.json', v + '/' + 'old_' + v)
    # set branches and devices
    devices = ''
    branch = ''
    if "stable_recovery" in v:
        branch = "1"
        devices = sr_devices
    elif "stable_fastboot" in v:
        branch = "F"
        devices = sf_devices
    elif "weekly_recovery" in v:
        branch = "0"
        devices = wr_devices
    elif "weekly_fastboot" in v:
        branch = "X"
        devices = wf_devices
    # fetch based on version
    if "_recovery" in v:
        recovery.fetch(devices, branch, folder, names)
    elif "_fastboot" in v:
        fastboot.fetch(devices, branch, folder, names)
    print("Fetched " + v.replace('_', ' '))

    if "stable_fastboot" in v:
        ao.main()

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

    # Compare
    print("Comparing")
    with open(v + '/' + 'old_' + v, 'r') as o, open(v + '/' + v + '.json', 'r') as n:
        diff = difflib.unified_diff(o.readlines(), n.readlines(), fromfile='old',
                                    tofile='new')
        changes = []
        for line in diff:
            if line.startswith('+') and 'filename' in line:
                changes.append(str(line))
        # save changes to file
        new = ''.join(changes).replace("+", "")
        with open(v + '/changes', 'w') as out:
            out.write(new)
        current = None
        if changes:
            # load the current data
            with open(v + '/' + v + '.json', 'r') as c:
                current = json.load(c)
            new = True
        else:
            print("No changes found!")
            if path.exists(v + '/' + 'changes'):
                remove(v + '/' + 'changes')
            new = False

    # commit, push and send
    if new:
        # Notify
        for i in changes:
            android = ''
            codename = ''
            device = ''
            link = ''
            md5 = ''
            version = ''
            rom = v.replace('_', ' ')
            telegram_message = ''
            discord_message = ''
            if "_recovery" in v:
                product = i.split('_')[1]
                for code_name, name in names.items():
                    if name[1] == product:
                        codename = code_name
                        product = name[1]
                for item in current:
                    try:
                        if product == str(item['filename']).split('_')[1]:
                            android = item['android']
                            codename = codename.split('_')[0]
                            device = item['device']
                            link = item['download']
                            version = item['version']
                    except IndexError:
                        continue
                    telegram_message = "New {} update available!\n" \
                                       "*Device:* {} \n" \
                                       "*Codename:* {} \n" \
                                       "*Version:* `{}` \n" \
                                       "*Android:* {} \n" \
                                       "*Download*: [Here]({}) \n" \
                                       "@MIUIUpdatesTracker | @XiaomiFirmwareUpdater" \
                        .format(rom, device, codename, version, android, link)
                    discord_message = "New {0} update available! \n \n" \
                                      "**Device**: {1} \n" \
                                      "**Codename**: {2} \n" \
                                      "**Version**: `{3}` \n" \
                                      "**Android**: {4} \n" \
                                      "**Download**: {5} \n" \
                                      "~~                                                     ~~" \
                        .format(rom, device, codename, version, android, link)

            elif "_fastboot" in v:
                codename = i.split('"')[3].split('_images_')[0]
                for item in current:
                    try:
                        if codename == str(item['filename']).split('_images_')[0]:
                            android = item['android']
                            codename = codename.split('_')[0]
                            device = item['device']
                            filesize = item['filesize']
                            link = item['download']
                            md5 = item['md5']
                            version = item['version']
                    except IndexError:
                        continue
                    telegram_message = "New {} image available!: \n" \
                                       "*Device:* {} \n" \
                                       "*Codename:* {} \n" \
                                       "*Version:* `{}` \n" \
                                       "*Android:* {} \n" \
                                       "*MD5:* `{}` \n" \
                                       "*Download:* [Here]({}) \n" \
                                       "@MIUIUpdatesTracker | @XiaomiFirmwareUpdater" \
                        .format(rom, device, codename, version, android, md5, link)
                    discord_message = "New {0} image available! \n \n" \
                                      "**Device**: {1} \n" \
                                      "**Codename**: {2} \n" \
                                      "**Version**: `{3}` \n" \
                                      "**Android**: {4} \n" \
                                      "**MD5**: `{5}` \n" \
                                      "**Download**: {6} \n" \
                                      "~~                                                     ~~" \
                        .format(rom, device, codename, version, android, md5, link)
            tg_post(telegram_message, codename)
            discord_post(discord_message, codename)
            # cleanup
            if path.exists(v + '/' + 'changes'):
                remove(v + '/' + 'changes')
    else:
        print(v + ": Nothing to do!")

# push
today = str(datetime.today()).split('.')[0]
system("git add *_recovery/*.json *_fastboot/*.json && "
       "git -c \"user.name=XiaomiFirmwareUpdater\" -c \"user.email=xiaomifirmwareupdater@gmail.com\" "
       "commit -m \"sync: {0}\" && "" \
       ""git push -q https://{1}@github.com/XiaomiFirmwareUpdater/miui-updates-tracker.git HEAD:master"
       .format(today, GIT_OAUTH_TOKEN))
