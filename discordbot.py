"""MIUI Updates Tracker - Discord bot script"""
import discord
from utils import is_roll_back, get_branch, get_region, get_type


class DiscordBot(discord.Client):
    """initialize Discord bot"""
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
        branch = get_branch(version)
        region = get_region(filename, codename, version)
        rom_type = get_type(filename)
        codename = codename.split('_')[0]
        device = device.replace(f' {region}', '')
        desc = f"**Device**: {device} \n" \
            f"**Codename**: `{codename}` \n" \
            f"**Region**: {region} \n" \
            f"**Version**: `{version} | {android}` \n" \
            f"**Size**: {filesize} \n" \
            f"**Download**: [Here]({download})"
        embed = discord.Embed(title=f"New {branch} {rom_type} update available!",
                              color=discord.Colour.orange(), description=desc)
        embed.set_footer(text=f"https://xiaomifirmwareupdater.com/miui/{codename}")
        device = device.lower()
        for name in self.channels:
            if device.startswith(name):
                await self.channels[name].send(embed=embed)
                print(f"Posted update for {codename} in Discord")
                return
        if device.startswith("redmi"):
            await self.channels['redmi other'].send(embed=embed)
            print(f"Posted update for {codename} in Discord")
        elif device.startswith("mi"):
            await self.channels['mi other'].send(embed=embed)
            print(f"Posted update for {codename} in Discord")

    async def on_ready(self):
        """Prepare"""
        print('Discord bot up!')
        self.channels = {x.name.replace('_series', '').replace('_', ' '): x
                         for x in self.get_all_channels()
                         if x.category is not None and ("mi" in x.category.name.lower() or "other" in x.category.name.lower())}
        for update in self.updates:
            if is_roll_back(update):
                continue
            await self.send_message(update)
        await self.logout()

    def send(self, updates):
        """send messages to Discord"""
        self.updates = updates
        self.run(self.token)
