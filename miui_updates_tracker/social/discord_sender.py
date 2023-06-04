import asyncio
import logging
from typing import List
from urllib.parse import quote

from discord import Client, Colour, Embed, HTTPException, Intents
from humanize import naturalsize

from miui_updates_tracker.common.constants import website
from miui_updates_tracker.common.database.database import get_device_name, get_full_name, get_incremental
from miui_updates_tracker.common.database.models.miui_update import Update

logger = logging.getLogger(__name__)
logging.getLogger('discord.client').setLevel(logging.ERROR)
logging.getLogger('discord.state').setLevel(logging.ERROR)
logging.getLogger('discord.gateway').setLevel(logging.ERROR)


class DiscordBot(Client):
    """
    This class implements discord bot that is used for sending updates to discord channels in Xiaomi server
    """

    def __init__(self, token):
        """
        Discord Bot class constructor
        :param token: Discord Bot API access token
        :param chat: Telegram chat username or id that will be used to send updates to
        """
        intents = Intents.default()
        intents.message_content = True
        super().__init__(loop=asyncio.get_running_loop(), intents=intents)
        self.token = token
        self.updates = None
        self.channels = None
        self._logger = logging.getLogger(__name__)

    async def send_message(self, update: Update):
        """
        Generates and sends a Discord message
        """
        short_codename = update.codename.split('_')[0]
        message = f"**Device**: {get_full_name(update.codename)}\n" \
                  f"**Codename**: `{short_codename}`\n" \
                  f"**Version**: `{update.version} | {update.android}`\n" \
                  f"**Size**: {naturalsize(update.size)}\n"
        if update.md5:
            message += f"**MD5**: `{update.md5}`\n"
        if update.changelog != "Bug fixes and system optimizations.":
            if len(update.changelog) + len(message) > 2000:
                branch = quote(update.branch.lower())
                message += f"**Changelog**: {website}/miui/{short_codename}/" \
                           f"{branch}/{update.version}/\n"
            else:
                message += f"**Changelog**:\n`{update.changelog}`\n"
        embed = Embed(title=f"New {update.branch} {update.method} update available!",
                      color=Colour.orange(), description=message)
        embed.add_field(name="Full ROM", value=f'[Download]({update.link})', inline=True)
        if update.method == "Recovery":
            incremental = get_incremental(update.version)
            if incremental:
                embed.add_field(name="Incremental", value=f'[Download]({incremental.link})', inline=True)
        embed.add_field(name="Latest", value=f'[Here]({website}/miui/{short_codename})', inline=True)
        embed.add_field(name="Archive", value=f'[Here]({website}/archive/miui/{short_codename})', inline=True)
        device = get_device_name(update.codename).lower()
        for name, channel in self.channels.items():
            if device.startswith(name):
                await channel.send(embed=embed)
                return
        await self.channels['other_xiaomi_phones'].send(embed=embed)

    async def on_ready(self):
        """Prepare"""
        self.channels = {x.name.replace('_series', '').replace('_', ' '): x
                         for x in sorted(self.get_all_channels(), key=lambda c: c.name)
                         if x.category_id == 699991467560534136}
        for update in self.updates:
            try:
                await self.send_message(update)
            except (KeyError, HTTPException) as e:
                self._logger.warning(f"Can't send discord message of update {update}.\n Error:{e}")
                continue
        await self.close()

    async def post_updates(self, new_updates: List[Update]):
        """
        Send updates to Discord channels
        :param new_updates: a list of updates
        """
        self.updates = new_updates
        await self.start(self.token)


async def run():
    from miui_updates_tracker import CONFIG
    updates = [Update(
        codename="lancelot", version="V11.0.4.0.QJCCNXM", android="10.0",
        branch="Stable", method="Recovery", size="2040109465",
        md5="89fd8abc76de4e216635e0cf29c15aed", filename="miui_LANCELOT_V11.0.4.0.QJCCNXM_89fd8abc76_10.0.zip",
        link="https://bigota.d.miui.com/V11.0.4.0.QJCCNXM/miui_LANCELOT_V11.0.4.0.QJCCNXM_89fd8abc76_10.0.zip",
        changelog="[Other]\nOptimized system performance\nImproved system security and stability"
    )]
    discord_bot = DiscordBot(CONFIG.get('discord').get('bot_token'))
    await discord_bot.post_updates(updates)


if __name__ == '__main__':
    asyncio.run(run())
