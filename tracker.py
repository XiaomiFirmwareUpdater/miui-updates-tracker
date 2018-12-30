import json
from datetime import date
from glob import glob
from os import remove, rename, path, environ, system

import recovery
from jsondiff import diff
from requests import post

import fastboot

# vars
GIT_OAUTH_TOKEN = environ['XFU']
bottoken = environ['bottoken']
telegram_chat = "@MIUIUpdatesTracker"
DISCORD_BOT_TOKEN = environ['DISCORD_BOT_TOKEN']
channelID = "484478392562089995"

# devices lists
sr_devices = {'aqua': '7.0', 'beryllium_global': '9.0', 'beryllium_ru_global': '8.1', 'cactus': '8.1',
              'cactus_global': '8.1', 'cancro': '6.0', 'cancro_global': '6.0', 'cancro_lte_ct': '6.0', 'cappu': '7.0',
              'capricorn': '8.0', 'capricorn_global': '7.0', 'cereus': '8.1', 'cereus_global': '8.1', 'chiron': '8.0',
              'chiron_global': '8.0', 'clover': '8.1', 'dipper': '8.1', 'dipper_global': '8.1',
              'dipper_ru_global': '8.1',
              'equuleus': '8.1', 'equuleus_global': '8.1', 'gemini': '8.0', 'gemini_global': '8.0', 'helium': '7.0',
              'helium_global': '7.0', 'hennessy': '5.0', 'hermes': '5.0', 'hermes_global': '5.0', 'hydrogen': '7.0',
              'hydrogen_global': '7.0', 'ido_xhdpi': '5.1', 'ido_xhdpi_global': '5.1', 'jason': '8.1',
              'jason_global': '7.1', 'kate_global': '6.0', 'kenzo': '6.0', 'kenzo_global': '6.0', 'land': '6.0',
              'land_global': '6.0', 'latte': '5.1', 'libra': '7.0', 'lithium': '8.0', 'lithium_global': '8.0',
              'markw': '6.0', 'markw_global': '6.0', 'meri': '7.1', 'mido': '7.0', 'mido_global': '7.0',
              'natrium': '8.0',
              'natrium_global': '8.0', 'nikel': '6.0', 'nikel_global': '6.0', 'nitrogen': '8.1',
              'nitrogen_global': '8.1',
              'omega': '6.0', 'oxygen': '7.1', 'oxygen_global': '7.1', 'perseus': '9.0', 'perseus_global': '9.0',
              'platina': '8.1', 'platina_global': '8.1', 'polaris': '9.0', 'polaris_global': '9.0',
              'polaris_ru_global': '8.0', 'prada': '6.0', 'prada_global': '6.0', 'riva': '7.1', 'riva_global': '7.1',
              'rolex': '6.0', 'rolex_global': '7.1', 'rosy': '7.1', 'rosy_global': '7.1', 'rosy_ru_global': '7.1',
              'sagit': '8.0', 'sagit_global': '8.0', 'sakura': '8.1', 'sakura_india_global': '8.1', 'santoni': '7.1',
              'santoni_global': '7.1', 'scorpio': '8.0', 'scorpio_global': '8.0', 'sirius': '8.1', 'tiffany': '7.1',
              'tulip_global': '8.1', 'ursa': '9.0', 'ugg': '7.1', 'ugg_global': '7.1', 'ugglite': '7.1',
              'ugglite_global': '7.1', 'vince': '7.1', 'vince_global': '8.1', 'vince_ru_global': '7.1', 'wayne': '8.1',
              'whyred': '8.1', 'whyred_global': '8.1', 'whyred_ru_global': '8.1', 'ysl': '8.1', 'ysl_global': '8.1',
              'ysl_ru_global': '8.1'}
sf_devices = ['aqua', 'beryllium_global', 'beryllium_ru_global', 'cactus', 'cactus_global', 'cancro', 'cancro_global',
              'cancro_lte_ct', 'cappu', 'capricorn', 'capricorn_global', 'cereus', 'cereus_global', 'chiron',
              'chiron_global', 'clover', 'dipper', 'dipper_global', 'dipper_ru_global', 'equuleus', 'equuleus_global',
              'gemini', 'gemini_global', 'helium', 'helium_global', 'hennessy', 'hermes', 'hermes_global', 'hydrogen',
              'hydrogen_global', 'ido_xhdpi', 'ido_xhdpi_global', 'jason', 'jason_global', 'kate_global', 'kenzo',
              'kenzo_global', 'land', 'land_global', 'latte', 'libra', 'lithium', 'lithium_global', 'markw',
              'markw_global', 'meri', 'mido', 'mido_global', 'natrium', 'natrium_global', 'nikel', 'nikel_global',
              'nitrogen', 'nitrogen_global', 'omega', 'oxygen', 'oxygen_global', 'perseus', 'platina',
              'platina_global', 'polaris', 'polaris_global', 'polaris_ru_global', 'prada', 'prada_global', 'riva',
              'riva_global', 'rolex', 'rolex_global', 'rosy', 'rosy_global', 'rosy_ru_global', 'sagit', 'sagit_global',
              'sakura', 'sakura_india_global', 'santoni', 'santoni_global', 'scorpio', 'scorpio_global', 'sirius',
              'tiffany', 'tulip_global', 'ursa', 'ugg', 'ugg_global', 'ugglite', 'ugglite_global', 'vince',
              'vince_global',
              'vince_ru_global', 'wayne', 'whyred', 'whyred_global', 'whyred_ru_global', 'ysl', 'ysl_global',
              'ysl_ru_global']
wr_devices = {'beryllium_global': '9.0', 'cactus': '8.1', 'cactus_global': '8.1', 'cappu': '7.0', 'capricorn': '8.0',
              'capricorn_global': '8.0', 'cereus': '8.1', 'cereus_global': '8.1', 'chiron': '8.0',
              'chiron_global': '8.0',
              'clover': '8.1', 'dipper': '9.0', 'dipper_global': '9.0', 'equuleus': '9.0', 'equuleus_global': '8.1',
              'gemini': '8.0', 'gemini_global': '8.0', 'helium': '7.0', 'helium_global': '7.0', 'hydrogen': '7.0',
              'hydrogen_global': '7.0', 'jason': '8.1', 'jason_global': '8.1', 'kate_global': '6.0', 'kenzo': '6.0',
              'kenzo_global': '6.0', 'land': '6.0', 'land_global': '6.0', 'lithium': '8.0', 'lithium_global': '8.0',
              'markw': '6.0', 'meri': '7.1', 'mido': '7.0', 'mido_global': '7.0', 'natrium': '8.0',
              'natrium_global': '8.0', 'nikel': '6.0', 'nikel_global': '6.0', 'nitrogen': '9.0',
              'nitrogen_global': '8.1',
              'omega': '6.0', 'oxygen': '7.1', 'oxygen_global': '7.1', 'perseus': '9.0', 'platina': '8.1',
              'platina_global': '8.1', 'polaris': '9.0', 'polaris_global': '9.0', 'prada': '6.0', 'riva': '8.1',
              'riva_global': '8.1', 'rolex': '6.0', 'rolex_global': '7.1', 'rosy': '8.1', 'rosy_global': '8.1',
              'sagit': '8.0', 'sagit_global': '8.0', 'sakura': '8.1', 'sakura_india_global': '8.1', 'santoni': '7.1',
              'santoni_global': '7.1', 'scorpio': '8.0', 'scorpio_global': '8.0', 'sirius': '9.0', 'tiffany': '8.1',
              'tulip_global': '8.1', 'ursa': '9.0', 'ugg': '7.1', 'ugg_global': '7.1', 'ugglite': '7.1',
              'ugglite_global': '7.1', 'vince': '8.1', 'vince_global': '8.1', 'wayne': '8.1', 'whyred': '8.1',
              'whyred_global': '8.1', 'ysl': '8.1',
              'ysl_global': '8.1'}
wf_devices = ['beryllium_global', 'cactus', 'cactus_global', 'cappu', 'capricorn', 'capricorn_global', 'cereus',
              'cereus_global', 'chiron', 'chiron_global', 'clover', 'dipper', 'dipper_global', 'equuleus',
              'equuleus_global', 'gemini', 'gemini_global', 'helium', 'helium_global', 'hydrogen', 'hydrogen_global',
              'jason', 'jason_global', 'kate_global', 'kenzo', 'kenzo_global', 'land', 'land_global', 'lithium',
              'lithium_global', 'markw', 'meri', 'mido', 'mido_global', 'natrium', 'natrium_global', 'nikel',
              'nikel_global', 'nitrogen', 'nitrogen_global', 'oxygen', 'oxygen_global', 'perseus', 'platina',
              'platina_global', 'polaris', 'polaris_global', 'prada', 'riva', 'riva_global', 'rolex', 'rolex_global',
              'rosy', 'rosy_global', 'sagit', 'sagit_global', 'sakura', 'sakura_india_global', 'santoni',
              'santoni_global', 'scorpio', 'scorpio_global', 'sirius', 'tiffany', 'tulip_global', 'ursa', 'ugg',
              'ugg_global', 'ugglite', 'ugglite_global', 'vince', 'vince_global', 'wayne', 'whyred', 'whyred_global',
              'ysl', 'ysl_global']

versions = ['stable_recovery', 'stable_fastboot', 'weekly_recovery', 'weekly_fastboot']

for v in versions:
    folder = v + '/'
    # backup old
    if path.exists(v + '/' + v + '.json'):
        rename(v + '/' + v + '.json', v + '/' + 'old_' + v)
    # set branches and devices
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
        recovery.fetch(devices, branch, folder)
    elif "_fastboot" in v:
        fastboot.fetch(devices, branch, folder)
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

    # Compare
    print("Comparing")
    with open(v + '/' + 'old_' + v, 'r') as o, open(v + '/' + v + '.json', 'r') as n:
        old = json.load(o)
        new = json.load(n)
        c = diff(old, new)
        if c:
            print("New changes found!")
            with open(v + '/' + 'changes', "w") as f:
                json.dump(c, f, indent=1)
            changes = True
        else:
            print("No changes found!")
            if path.exists(v + '/' + 'changes'):
                remove(v + '/' + 'changes')
            changes = False

    # commit, push and send
    if changes is True:
        today = str(date.today())
        db = v + '/' + v + '.json'
        system("git add {0} && "" \
               ""git commit -m \"sync: {1}\" --author='XiaomiFirmwareUpdater <xiaomifirmwareupdater@gmail.com>' && "" \
               ""git push -q https://{2}@github.com/XiaomiFirmwareUpdater/miui-updates-tracker.git HEAD:master"
               .format(db, today, GIT_OAUTH_TOKEN))
        # Notify
        rom = str(v.replace('_', ' '))
        if "_recovery" in v:
            for key, value in c.items():
                if "Global" in str(value['filename']):
                    region = "Global"
                else:
                    region = "China"
                android = str(value['filename']).split('_')[4].replace('.zip', ' ')
                device = str(value['filename']).split('_')[1]
                version = value['version']
                link = value['download']
                telegram_message = "New {0} update available!: \n" \
                                   "*Device:* {1} \n" \
                                   "*Version:* `{2}` \n" \
                                   "*Type:* {3} \n" \
                                   "*Android:* {4} \n" \
                                   "Download: [Here]({5}) \n" \
                                   "@MIUIUpdatesTracker | @XiaomiFirmwareUpdater" \
                    .format(rom, device, version, region, android, link)
                discord_message = "New {0} update available! \n \n" \
                                  "**Codename**: {1} \n" \
                                  "**Version**: `{2}` \n" \
                                  "**Type:** {3} \n" \
                                  "**Android**: {4} \n" \
                                  "**Download**: {5} \n" \
                                  "~~                                                     ~~" \
                    .format(rom, device, version, region, android, link)
        elif "_fastboot" in v:
            for key, value in c.items():
                if "_cn_" in str(value['filename']):
                    region = "China"
                    android = str(value['filename']).split('_')[4]
                else:
                    region = "Global"
                    android = str(value['filename']).split('_')[5]
                device = str(value['filename']).split('_')[0]
                version = value['version']
                md5 = value['md5']
                link = value['download']
                telegram_message = "New {0} image available!: \n" \
                                   "*Device:* {1} \n" \
                                   "*Version:* `{2}` \n" \
                                   "*Type:* {3} \n" \
                                   "*Android:* {4} \n" \
                                   "*MD5:* `{5}` \n" \
                                   "Download: [Here]({6}) \n" \
                                   "@MIUIUpdatesTracker | @XiaomiFirmwareUpdater" \
                    .format(rom, device, version, region, android, md5, link)
                discord_message = "New {0} image available! \n \n" \
                                  "**Device**: {1} \n" \
                                  "**Version**: `{2}` \n" \
                                  "**Type:** {3} \n" \
                                  "**Android**: {4} \n" \
                                  "**MD5**: `{5}` \n" \
                                  "**Download**: {6} \n" \
                                  "~~                                                     ~~" \
                    .format(rom, device, version, region, android, md5, link)

        params = (
            ('chat_id', telegram_chat),
            ('text', telegram_message),
            ('parse_mode', "Markdown"),
            ('disable_web_page_preview', "yes")
        )
        telegram_url = "https://api.telegram.org/bot" + bottoken + "/sendMessage"
        telegram_req = post(telegram_url, params=params)
        telegram_status = telegram_req.status_code
        if telegram_status == 200:
            print("{0}: Telegram Message sent".format(device))
        else:
            print("Telegram Error")

        discord_url = "https://discordapp.com/api/channels/{}/messages".format(channelID)
        headers = {"Authorization": "Bot {}".format(DISCORD_BOT_TOKEN),
                   "User-Agent": "myBotThing (http://some.url, v0.1)",
                   "Content-Type": "application/json", }
        data = json.dumps({"content": discord_message})
        discord_req = post(discord_url, headers=headers, data=data)
        discord_status = discord_req.status_code
        if discord_status == 200:
            print("{0}: Discord Message sent".format(device))
        else:
            print("Discord Error")
        if path.exists(v + '/' + 'changes'):
            remove(v + '/' + 'changes')
    elif changes is False:
        print(v + ": Nothing to do!")
