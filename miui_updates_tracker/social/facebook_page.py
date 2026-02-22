from typing import List

from facebook import GraphAPI
from miui_updates_tracker import CONFIG
from miui_updates_tracker.common.constants import website
from miui_updates_tracker.common.database.database import get_device_name, get_full_name, get_incremental
from miui_updates_tracker.common.database.models.miui_update import Update
from miui_updates_tracker.utils.helpers import safe_naturalsize


class FacebookPage:
    def __init__(self, page_id, page_token):
        self.page_id = page_id
        self.graph = GraphAPI(access_token=page_token, version="3.0")

    def post(self, text, link):
        self.graph.put_object(self.page_id, "feed", message=text, link=link)

    @staticmethod
    def generate_post(update: Update) -> (str, str):
        os_name = "HyperOS" if bool(update.version.startswith("OS")) else "MIUI"
        short_codename = update.codename.split('_')[0]
        link = f"{website}/miui/{short_codename}"
        message: str = f"New {update.branch} {update.method} update available for " \
                       f"{get_full_name(update.codename)} ({short_codename})!\n\n"
        message += f"Version: {update.version} | {update.android}\n" \
                   f"Size: {safe_naturalsize(update.size)}\n"
        if update.md5:
            message += f"MD5: {update.md5}\n"
        message += f"\nFull Update: {update.link}\n"
        # incremental update
        if update.method == "Recovery":
            incremental = get_incremental(update.version)
            if incremental:
                message += f"\nIncremental Update: {incremental.link}\n"
        if update.changelog != "Bug fixes and system optimizations.":
            message += f"\nChangelog:\n{update.changelog}\n"
        message += f"\n#{os_name}_Updates #Xiaomi #{os_name} #{get_device_name(update.codename).replace(' ', '')}"
        if update.version[0].isalpha():
            message += f" #{os_name}{update.version.split('.')[0][1:].split('.')[0]}"
        message += f" #Android{update.android.split('.')[0]}"
        return message, link

    async def post_updates(self, new_updates: List[Update]):
        """
        Send updates to a Telegram chat
        :param new_updates: a list of updates
        """
        for update in new_updates:
            text, link = self.generate_post(update)
            self.post(text, link)


if __name__ == '__main__':
    facebook_config: dict = CONFIG.get('facebook')
    if None not in facebook_config.values():
        facebook_page = FacebookPage(facebook_config.get('page_id'), facebook_config.get('page_token'))
        facebook_page.post("XiaomiFirmwareUpdater", website)
