import discord
from os import environ

class DiscordBot(discord.Client):
    def __init__(self, token):
        super().__init__()
        self.token = token
        self.updates = None
        self.channels = None

    async def send_message(self, update: dict):
        """
        Generates and sends a Discord message
        """
        android = update['android']
        codename = update['codename']
        device = update['device']
        filename = update['filename']
        filesize = update['size']
        version = update['version']
        download = update['download']
        if 'V' in version:
            branch = 'Stable'
        else:
            branch = 'Developer'
        if 'eea_global' in filename or 'eea_global' in codename or 'EU' in version:
            region = 'EEA'
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
        device = device.replace(f' {region}', '')
        desc = f"**Device**: {device} \n" \
            f"**Codename**: `{codename}` \n" \
            f"**Region**: {region} \n" \
            f"**Version**: `{version} | {android}` \n" \
            f"**Size**: {filesize} \n" \
            f"**Download**: [Here]({download})"
        embed = discord.Embed(title=f"New {branch} {rom_type} update available!", color=discord.Colour.orange(), description=desc)
        embed.set_footer(text="@MIUIUpdatesTracker | @XiaomiFirmwareUpdater")
        device = device.lower()
        for name in self.channels:
            if device.startswith(name):
                await self.channels[name].send(embed=embed)
                return
        if device.startswith("redmi"):
            await self.channels['redmi other'].send(embed=embed)
        elif device.startswith("mi"):
            await self.channels['mi other'].send(embed=embed)
        elif device.starswith("poco"):
            await self.channels['pocophone f1'].send(embed=embed)

    async def on_ready(self):
        print('Discord bot up!')
        self.channels = {x.name.replace('_series', '').replace('_', ' '): x for x in self.get_all_channels() if x.category is not None and "phones" in x.category.name}
        for update in self.updates:
            await self.send_message(update)
        await self.logout()
    
    def send(self, updates):
        self.updates = updates
        self.run(self.token)
