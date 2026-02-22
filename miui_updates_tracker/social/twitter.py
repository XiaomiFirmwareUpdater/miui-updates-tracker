import logging
from asyncio import sleep
from typing import Dict, List
from urllib.parse import quote

from miui_updates_tracker.common.constants import website
from miui_updates_tracker.common.database.database import get_device_name, get_full_name
from miui_updates_tracker.common.database.models.miui_update import Update
from miui_updates_tracker.utils.helpers import safe_naturalsize
from tweepy import API, OAuthHandler, TweepyException
from tweepy.models import Status


class TwitterBot:
    tweet_max: int
    api: API

    def __init__(self, config: Dict[str, str]):
        # Authenticate to Twitter
        auth = OAuthHandler(config.get("consumer_key"), config.get("consumer_secret"))
        auth.set_access_token(config.get("access_token"), config.get("access_token_secret"))
        # Create API object
        self.api = API(auth)
        self.tweet_max = 280
        self._logger = logging.getLogger(__name__)

    def generate_posts(self, update: Update) -> List[str]:
        os_name = "HyperOS" if bool(update.version.startswith("OS")) else "MIUI"
        footer = f"\n#{os_name}_Updates #Xiaomi #{os_name} #{get_device_name(update.codename).replace(' ', '')}"
        if update.version[0].isalpha():
            footer += f" #{os_name}{update.version.split('.')[0][1:].split('.')[0]}"
        footer += f" #Android{update.android.split('.')[0]}"
        posts = []
        short_codename = update.codename.split('_')[0]
        message: str = f"New {update.branch} {update.method} update available for " \
                       f"{get_full_name(update.codename)} ({short_codename})!\n"
        message += f"Version: {update.version} | {update.android}\n" \
                   f"Size: {safe_naturalsize(update.size)}\n"
        if update.md5:
            message += f"MD5: {update.md5}\n"
        message_2 = ""
        download = f"Download: {update.link}\n"
        if len(message + download) < self.tweet_max:
            message += download
        else:
            message_2 += download
        if update.changelog != "Bug fixes and system optimizations.":
            if len(update.changelog) + len(message) > self.tweet_max:
                branch = quote(update.branch.lower())
                message_2 += f"Changelog: {website}/miui/{short_codename}/" \
                             f"{branch}/{update.version}/\n"
            else:
                message_2 += f"Changelog:\n{update.changelog}\n"
        posts.append(message)
        if len(message_2) > self.tweet_max:
            message_2 = message_2[:self.tweet_max - len(footer)]
            message_2 += footer
        else:
            if message_2:
                message_2 += footer
                posts.append(message_2)
        return posts

    async def tweet(self, text, reply=None):
        try:
            if reply:
                return self.api.update_status(text, in_reply_to_status_id=reply)
            return self.api.update_status(text)
        except TweepyException as e:
            self._logger.warning(f"Can't send twitter message {text}.\n Error:{e}")

    async def post_updates(self, new_updates: List[Update]):
        """
        Post updates to Twitter
        :param new_updates: a list of updates
        :return: None
        """
        for update in new_updates:
            posts = self.generate_posts(update)
            previous = None
            for post in posts:
                if previous:
                    tweet: Status = await self.tweet(post, reply=previous)
                    previous = tweet.id
                else:
                    tweet: Status = await self.tweet(post)
                    previous = tweet.id
                await sleep(60)
