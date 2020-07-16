from time import sleep
from typing import Dict, List

from humanize import naturalsize
from tweepy import OAuthHandler, API, Status

from miui_updates_tracker.common.database.database import get_full_name, get_device_name
from miui_updates_tracker.common.database.models.update import Update


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

    def generate_posts(self, update: Update) -> List[str]:
        footer = f"\n#MIUI_Updates #Xiaomi #MIUI #{get_device_name(update.codename).replace(' ', '')}"
        if update.version.startswith("V"):
            footer += f" #MIUI{update.version.split('V')[1].split('.')[0]}"
        footer += f" #Android{update.android.split('.')[0]}"
        posts = []
        short_codename = update.codename.split('_')[0]
        message: str = f"New {update.branch} {update.method} update available for " \
                       f"{get_full_name(update.codename)} ({short_codename})!\n"
        message += f"Version: {update.version} | {update.android}\n" \
                   f"Size: {naturalsize(update.size)}\n"
        if update.md5:
            message += f"MD5: {update.md5}\n"
        message_2 = ""
        download = f"Download: {update.link}\n"
        if len(message + download) < self.tweet_max:
            message += download
        else:
            message_2 += download
        if update.changelog != "Bug fixes and system optimizations.":
            message_2 += f"Changelog:\n{update.changelog}"
        posts.append(message)
        if len(message_2) > self.tweet_max:
            message_2 = message_2[:self.tweet_max - len(footer)]
            message_2 += footer
        else:
            if message_2:
                message_2 += footer
                posts.append(message_2)
        return posts

    def tweet(self, text, reply=None):
        if reply:
            return self.api.update_status(text, reply)
        return self.api.update_status(text)

    def post_updates(self, new_updates: List[Update]):
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
                    tweet: Status = self.tweet(post, reply=previous)
                    previous = tweet.id
                else:
                    tweet: Status = self.tweet(post)
                    previous = tweet.id
                sleep(60)
