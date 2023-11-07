import asyncio
import logging
import re
from itertools import groupby
from pathlib import Path
from string import Template
from typing import List
from urllib.parse import quote

import yaml
from aiohttp.client_exceptions import ServerDisconnectedError
from humanize import naturalsize

from miui_updates_tracker.common.constants import website
from miui_updates_tracker.common.database.database import get_device_roms, get_full_name, get_incremental
from miui_updates_tracker.common.database.models.miui_update import Update
from miui_updates_tracker.social.xda_poster.xda import XDA

current_dir = Path(__file__).parent.absolute()


class XDAPoster(XDA):
    """XDA API client"""

    def __init__(self, api_key):
        with open(f'{current_dir}/xda_threads.yml', 'r') as file:
            self.threads = yaml.load(file, Loader=yaml.CLoader)
        with open(f'{current_dir}/xda_update_template.txt', 'r') as template:
            self.update_template: Template = Template(template.read())
        with open(f'{current_dir}/xda_thread_template.txt', 'r') as template:
            self.thread_template: Template = Template(template.read())
        super().__init__(api_key)

    def generate_message(self, update: Update) -> str:
        """
        Generate an update message from and `Update` object
        :param update: an Update object that contains update's information from official website
        :return: A string containing the update's message
        """
        short_codename = update.codename.split('_')[0]
        # incremental update
        incremental = None
        if update.method == "Recovery":
            incremental = get_incremental(update.version)

        return self.update_template.substitute(
            type=f"{update.branch} {update.method}",
            device=get_full_name(update.codename),
            codename=short_codename,
            version=update.version,
            android=update.android,
            date=update.date,
            zip_size=naturalsize(update.size),
            md5_hash=update.md5 if update.md5 else "Unknown",
            link=update.link,
            incremental_link=f'[URL="{incremental.link}"]Here[/URL]' if incremental else "Unavailable",
            changelog=update.changelog
        )

    def generate_thread(self, codename: str) -> str:
        """
        Generate an thread body for a codename
        :param codename: devices codename
        :return: A string containing the update's message
        """
        updates = get_device_roms(codename)
        grouped_by_name = [list(item) for _, item in
                           groupby(sorted(updates, key=lambda x: x.name), lambda x: x.name)]
        updates_history = ""
        for group in grouped_by_name:
            updates_history += f"[B]{group[0].name}[/B]\n"
            updates_history += "[LIST]\n"
            for update in group:
                updates_history += f"[*]{update.date} | {update.branch} {update.method} | {update.version} | " \
                                   f"[URL='{update.link}']Download[/URL] | " \
                                   f"[URL='{website}/miui/{codename}/{quote(update.branch.lower())}/" \
                                   f"{update.version}/']Details[/URL]\n"
            updates_history += "[/LIST]\n"
        device_name: str = ' / '.join(list(set([' '.join(i.name.split(' ')[:-1]) for i in updates])))
        thread = self.thread_template.substitute(codename=codename, device_name=device_name,
                                                 updates_history=updates_history)
        if len(thread) > 60000:
            thread = re.sub(r'\[\*\]201(?:8|9).*\n', '', thread)
        return thread

    async def post_updates(self, new_updates: List[Update]):
        """
        Send updates to an XDA thread
        :param new_updates: a list of updates
        :return: None
        """
        # new_updates = sorted(new_updates, key=lambda x: x.date, reverse=True)[:1]
        for update in new_updates:
            codename = update.codename.split('_')[0]
            if codename not in self.threads.keys():
                continue
            xda_post = self.generate_message(update)
            try:
                await self.post_async(self.threads[codename]['thread'], xda_post)
                await asyncio.sleep(15)
            except ServerDisconnectedError:
                logging.error(f"Server disconnected while posting {update}.")
        updated_devices = list(set([i.codename.split('_')[0] for i in new_updates]))
        for device in updated_devices:
            if device not in self.threads.keys():
                continue
            xda_thread = self.generate_thread(device)
            try:
                await self.update_post_async(self.threads[device]['post'], xda_thread)
                await asyncio.sleep(15)
            except ServerDisconnectedError:
                logging.error(f"Server disconnected while updating {device} thread.")
        # print("Done")


async def main():
    from miui_updates_tracker import CONFIG
    from miui_updates_tracker.common.database import close_db
    from miui_updates_tracker.common.database.database import get_device_latest
    all_updates = list(filter(lambda x: x.date, get_device_latest('odin')))
    xda = XDAPoster(CONFIG['xda']['access_token'])
    await xda.post_updates(all_updates)
    close_db()


def run():
    """asyncio trigger function"""
    event_loop = asyncio.get_event_loop()
    event_loop.run_until_complete(main())


if __name__ == '__main__':
    run()
