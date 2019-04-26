import difflib
import json
from datetime import datetime
from glob import glob
from os import remove, rename, path, environ, system

import fastboot
import recovery
from requests import post


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

# devices lists
names = {'beryllium_global': ('Poco F1 Global', 'POCOF1Global'), 'cactus': ('Redmi 6A China', 'HM6A'),
         'cactus_global': ('Redmi 6A Global', 'HM6AGlobal'), 'cappu': ('Mi Pad 3 China', 'MIPAD3'),
         'capricorn': ('Mi 5s China', 'MI5S'), 'capricorn_global': ('Mi 5s Global', 'MI5SGlobal'),
         'cereus': ('Redmi 6 China', 'HM6'), 'cereus_global': ('Redmi 6 Global', 'HM6Global'),
         'cepheus': ('Mi 9 China', 'CEPHEUS'), 'cepheus_global': ('Mi 9 Global', 'CEPHEUSGlobal'),
         'cepheus_eea_global': ('Mi 9 Global EEA', 'CEPHEUSEEAGlobal'), 'chiron': ('Mi MIX 2 China', 'MIMIX2'),
         'chiron_global': ('Mi MIX 2 Global', 'MIMIX2Global'), 'clover': ('Mi Pad 4 (Plus) China', 'MIPAD4'),
         'dipper': ('Mi 8 China', 'MI8'), 'dipper_global': ('Mi 8 Global', 'MI8Global'),
         'equuleus': ('Mi 8 Pro China', 'MI8UD'), 'equuleus_global': ('Mi 8 Pro Global', 'MI8UDGlobal'),
         'grus': ('Mi 9 SE', 'GRUS'), 'helium': ('Mi Max Prime China', 'MIMAX652'),
         'helium_global': ('Mi Max Prime Global', 'MIMAX652Global'), 'hydrogen': ('Mi Max China', 'MIMAX'),
         'hydrogen_global': ('Mi Max Global', 'MIMAXGlobal'), 'jason': ('Mi Note 3 China', 'MINote3'),
         'jason_global': ('Mi Note 3 Global', 'MINote3Global'),
         'kate_global': ('Redmi Note 3 SE Global', 'HMNote3ProtwGlobal'), 'land': ('Redmi 3S China', 'HM3S'),
         'land_global': ('Redmi 3S Global', 'HM3SGlobal'), 'lavender': ('Redmi Note 7 China', 'LAVENDER'),
         'lavender_global': ('Redmi Note 7 Global', 'LAVENDERGlobal'),
         'lavender_eea_global': ('Redmi Note 7 EEA Global', 'LAVENDEREEAGlobal'),
         'lavender_in_global': ('Redmi Note 7 India', 'LAVENDERINGlobal'),
         'lithium': ('Mi MIX China', 'MIMIX'), 'lithium_global': ('Mi MIX Global', 'MIMIXGlobal'),
         'lotus': ('Mi Play', 'MIPLAY'), 'markw': ('Redmi 4 Prime China', 'HM4Pro'),
         'markw_global': ('Redmi 4 Prime Global', 'HM4ProGlobal'), 'meri': ('Mi 5C China', 'MI5C'),
         'mido': ('Redmi Note 4 China', 'HMNote4X'), 'mido_global': ('Redmi Note 4 Global', 'HMNote4XGlobal'),
         'natrium': ('Mi 5s Plus China', 'MI5SPlus'), 'natrium_global': ('Mi 5s Plus Global', 'MI5SPlusGlobal'),
         'nikel': ('Redmi Note 4 MTK China', 'HMNote4'), 'nikel_global': ('Redmi Note 4 MTK Global', 'HMNote4Global'),
         'nitrogen': ('Mi Max 3 China', 'MIMAX3'), 'nitrogen_global': ('Mi Max 3 Global', 'MIMAX3Global'),
         'onclite': ('Redmi 7 China', 'ONCLITE'), 'onclite_global': ('Redmi 7 Global', 'ONCLITEGlobal'),
         'onclite_eea_global': ('Redmi 7 EEA Global', 'ONCLITEEEAGlobal'), 'onc_in_global': ('Redmi Y3 India', 'ONCINGlobal'),
         'omega': ('Redmi Pro China', 'HMPro'), 'oxygen': ('Mi Max 2 China', 'MIMAX2'),
         'oxygen_global': ('Mi Max 2 Global', 'MIMAX2Global'), 'perseus': ('Mi MIX 3 China', 'MIMIX3'),
         'perseus_global': ('Mi MIX 3 Global', 'MIMIX3Global'), 'platina': ('Mi 8 Lite China', 'MI8Lite'),
         'platina_global': ('Mi 8 Lite Global', 'MI8LiteGlobal'), 'polaris': ('Mi MIX 2S China', 'MIMIX2S'),
         'polaris_global': ('Mi MIX 2S Global', 'MIMIX2SGlobal'), 'prada': ('Redmi 4 China', 'HM4'),
         'prada_global': ('Redmi 4 Global', 'HM4Global'), 'riva': ('Redmi 5A China', 'HM5A'),
         'riva_global': ('Redmi 5A Global', 'HM5AGlobal'), 'rolex': ('Redmi 4A China', 'HM4A'),
         'rolex_global': ('Redmi 4A Global', 'HM4AGlobal'), 'rosy': ('Redmi 5 China', 'HM5'),
         'rosy_global': ('Redmi 5 Global', 'HM5Global'), 'sagit': ('Mi 6 China', 'MI6'),
         'sagit_global': ('Mi 6 Global', 'MI6Global'), 'sakura': ('Redmi 6 Pro China', 'HM6Pro'),
         'sakura_india_global': ('Redmi 6 Pro India', 'HM6ProINGlobal'), 'santoni': ('Redmi 4X China', 'HM4X'),
         'santoni_global': ('Redmi 4X Global', 'HM4XGlobal'), 'scorpio': ('Mi Note 2 China', 'MINote2'),
         'scorpio_global': ('Mi Note 2 Global', 'MINote2Global'), 'sirius': ('Mi 8 SE China', 'MI8SE'),
         'tiffany': ('Mi 5X China', 'MI5X'), 'tulip_global': ('Redmi Note 6 Pro Global', 'HMNote6ProGlobal'),
         'ugg': ('Redmi Note 5A Prime China', 'HMNote5A'),
         'ugg_global': ('Redmi Note 5A Prime Global', 'HMNote5AGlobal'),
         'ugglite': ('Redmi Note 5A (2GB) China', 'HMNote5ALITE'),
         'ugglite_global': ('Redmi Note 5A (2GB) Global', 'HMNote5ALITEGlobal'),
         'ursa': ('Mi 8 Explorer China', 'MI8Explorer'), 'vince': ('Redmi 5 Plus China', 'HM5Plus'),
         'vince_global': ('Redmi 5 Plus Global - Redmi Note 5 India', 'HM5PlusGlobal'),
         'violet': ('Redmi Note 7 Pro China', 'VIOLET'),
         'violet_in_global': ('Redmi Note 7 Pro India', 'VIOLETINGlobal'),
         'wayne': ('Mi 6X China', 'MI6X'), 'whyred': ('Redmi Note 5 China', 'HMNote5'),
         'whyred_global': ('Redmi Note 5 Global - Redmi Note 5 Pro India', 'HMNote5HMNote5ProGlobal'),
         'ysl': ('Redmi S2 China', 'HMS2'), 'ysl_global': ('Redmi S2 Global - Redmi Y2', 'HMS2Global')}
sr_devices = {'beryllium_global': '9.0', 'cactus': '8.1', 'cactus_global': '8.1', 'cappu': '7.0', 'capricorn': '8.0',
              'capricorn_global': '7.0', 'cereus': '8.1', 'cereus_global': '8.1', 'cepheus': '9.0',
              'cepheus_global': '9.0',
              'cepheus_eea_global': '9.0', 'chiron': '8.0', 'chiron_global': '8.0', 'clover': '8.1', 'dipper': '9.0',
              'dipper_global': '9.0', 'equuleus': '9.0', 'equuleus_global': '9.0', 'grus': '9.0', 'helium': '7.0',
              'helium_global': '7.0', 'hydrogen': '7.0', 'hydrogen_global': '7.0', 'jason': '8.1',
              'jason_global': '8.1', 'kate_global': '6.0', 'land': '6.0', 'land_global': '6.0', 'lavender': '9.0', 
              'lavender_global': '9.0', 'lavender_eea_global': '9.0', 'lavender_in_global': '9.0', 'lithium': '8.0', 'lithium_global': '8.0',
              'lotus': '8.1', 'markw': '6.0', 'markw_global': '6.0', 'meri': '7.1', 'mido': '7.0', 'mido_global': '7.0',
              'natrium': '8.0', 'natrium_global': '8.0', 'nikel': '6.0', 'nikel_global': '6.0', 'nitrogen': '8.1',
              'nitrogen_global': '9.0', 'onclite': '9.0', 'onclite_global': '9.0', 'omega': '6.0', 'oxygen': '7.1',
              'oxygen_global': '7.1','perseus': '9.0',
              'perseus_global': '9.0', 'platina': '9.0', 'platina_global': '9.0', 'polaris': '9.0',
              'polaris_global': '9.0', 'prada': '6.0', 'prada_global': '6.0', 'riva': '8.1', 'riva_global': '7.1',
              'rolex': '6.0', 'rolex_global': '7.1', 'rosy': '8.1', 'rosy_global': '7.1', 'sagit': '8.0',
              'sagit_global': '8.0', 'sakura': '9.0', 'sakura_india_global': '8.1', 'santoni': '7.1',
              'santoni_global': '7.1', 'scorpio': '8.0', 'scorpio_global': '8.0', 'sirius': '9.0', 'tiffany': '8.1',
              'tulip_global': '8.1', 'ursa': '9.0', 'ugg': '7.1', 'ugg_global': '7.1', 'ugglite': '7.1',
              'ugglite_global': '7.1', 'vince': '8.1', 'vince_global': '8.1', 'violet': '9.0',
              'violet_in_global': '9.0',
              'wayne': '8.1', 'whyred': '8.1', 'whyred_global': '8.1', 'ysl': '8.1', 'ysl_global': '8.1'}
sf_devices = ['beryllium_global', 'cactus', 'cactus_global', 'cappu', 'capricorn', 'capricorn_global', 'cereus',
              'cereus_global', 'cepheus', 'cepheus_eea_global', 'chiron', 'chiron_global', 'clover', 'dipper',
              'dipper_global', 'equuleus', 'equuleus_global', 'grus', 'helium', 'helium_global', 'hydrogen',
              'hydrogen_global', 'jason', 'jason_global', 'kate_global', 'land', 'land_global',
              'lavender', 'lavender_global', 'lavender_eea_global', 'lavender_in_global', 'lithium', 'lithium_global',
              'lotus', 'markw', 'markw_global', 'meri', 'mido',
              'mido_global', 'natrium', 'natrium_global', 'nikel', 'nikel_global', 'nitrogen', 'nitrogen_global',
              'onclite', 'onclite_global' 'onclite_eea_global'
              'omega', 'oxygen', 'oxygen_global', 'perseus', 'perseus_global', 'platina', 'platina_global', 'polaris', 'polaris_global',
              'prada', 'prada_global', 'riva', 'riva_global', 'rolex', 'rolex_global', 'rosy', 'rosy_global', 'sagit',
              'sagit_global', 'sakura', 'santoni', 'santoni_global', 'scorpio', 'scorpio_global',
              'sirius', 'tiffany', 'tulip_global', 'ursa', 'ugg', 'ugg_global', 'ugglite', 'ugglite_global',
              'violet', 'violet_in_global', 'vince', 'vince_global', 'wayne', 'whyred', 'whyred_global', 'ysl',
              'ysl_global']
wr_devices = {'beryllium_global': '9.0', 'cactus': '8.1', 'cactus_global': '8.1', 'cappu': '7.0', 'capricorn': '8.0',
              'capricorn_global': '8.0', 'cereus': '8.1', 'cereus_global': '8.1', 'cepheus': '9.0',
              'cepheus_global': '9.0', 'chiron': '8.0',
              'chiron_global': '8.0', 'clover': '8.1', 'dipper': '9.0', 'dipper_global': '9.0', 'equuleus': '9.0',
              'equuleus_global': '9.0', 'jason': '8.1', 'jason_global': '8.1', 
              'lavender': '9.0', 'lithium': '8.0', 'lithium_global': '8.0', 'lotus': '8.1',
              'meri': '7.1', 'mido': '7.0', 'mido_global': '7.0', 'natrium': '8.0', 'natrium_global': '8.0', 'nitrogen': '9.0',
              'nitrogen_global': '9.0', 'oxygen': '7.1', 'oxygen_global': '7.1', 'perseus': '9.0',
              'perseus_global': '9.0', 'platina': '9.0', 'platina_global': '9.0', 'polaris': '9.0', 'polaris_global': '9.0',
              'riva': '8.1', 'riva_global': '8.1', 'rolex': '6.0', 'rolex_global': '7.1', 'rosy': '8.1',
              'rosy_global': '8.1', 'sagit': '8.0', 'sagit_global': '8.0', 'sakura': '9.0',
              'sakura_india_global': '9.0', 'santoni': '7.1', 'santoni_global': '7.1', 'scorpio': '8.0',
              'scorpio_global': '8.0', 'sirius': '9.0', 'tiffany': '8.1', 'tulip_global': '9.0', 'ursa': '9.0',
              'ugg': '7.1', 'ugg_global': '7.1', 'ugglite': '7.1', 'ugglite_global': '7.1', 'vince': '8.1',
              'vince_global': '8.1', 'wayne': '9.0', 'whyred': '9.0', 'whyred_global': '9.0', 'ysl': '8.1',
              'ysl_global': '8.1'}
wf_devices = ['beryllium_global', 'cactus', 'cactus_global', 'cappu', 'capricorn', 'capricorn_global', 'cereus',
              'cereus_global', 'cepheus', 'cepheus_global', 'chiron', 'chiron_global', 'clover', 'dipper',
              'dipper_global', 'equuleus', 'equuleus_global', 'jason', 'jason_global',
              'lavender', 'lithium', 'lithium_global', 'lotus', 'meri', 'mido', 'mido_global', 'natrium',
              'natrium_global', 'nitrogen', 'nitrogen_global', 'oxygen', 'oxygen_global', 'perseus', 'perseus_global',
              'platina', 'platina_global', 'polaris', 'polaris_global',
              'riva', 'riva_global', 'rolex', 'rolex_global', 'rosy', 'rosy_global', 'sagit', 'sagit_global', 'sakura',
              'santoni', 'santoni_global', 'scorpio', 'scorpio_global', 'sirius', 'tiffany',
              'tulip_global', 'ursa', 'ugg', 'ugg_global', 'ugglite', 'ugglite_global', 'vince', 'vince_global',
              'wayne', 'whyred', 'whyred_global', 'ysl', 'ysl_global']
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
