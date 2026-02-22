import asyncio
from datetime import datetime, timezone
from typing import Dict

from feedgen.feed import FeedGenerator
from miui_updates_tracker import CONF_DIR
from miui_updates_tracker.common.constants import website
from miui_updates_tracker.common.database.database import get_incremental, get_all_latest_updates
from miui_updates_tracker.utils.helpers import safe_naturalsize


class RSSGenerator:
    feeds: Dict[str, FeedGenerator]
    updates: list

    def __init__(self, updates):
        self.updates = updates
        self.feeds = {}

    @staticmethod
    def add_feed_entry(feed, update):
        entry = feed.add_entry()
        entry.title(f"MIUI {update.version} {update.method} update for {update.fullname}")
        entry.link(href=update.link, rel='alternate')
        try:
            entry.pubDate(datetime.combine(update.date, datetime.min.time(), tzinfo=timezone.utc))
        except TypeError:
            entry.pubDate(datetime.combine(datetime.today(), datetime.min.time(), tzinfo=timezone.utc))
        description = f"<p<b>New {update.branch} {update.method} update available!</b></p>\n" \
                      f"<p><b>Device:</b> {update.fullname}</p>\n" \
                      f"<p><b>Codename:</b> {update.codename.split('_')[0]}</p>\n" \
                      f"<p><b>Version:</b> {update.version} | {update.android}</p>\n" \
                      f"<p><b>Size:</b> {safe_naturalsize(update.size)}</p>\n" \
                      f"<p><b>MD5:</b> {update.md5}</p>\n" \
                      f"<p><b>Changelog:</b><br>" + '<br>'.join(update.changelog.splitlines()) + \
                      f"</p>\n<p><b>Download:</b> <a href='{update.link}'>Here</a></p>"
        if update.method == "Recovery":
            incremental = get_incremental(update.version)
            if incremental:
                description += f"<p><b>Incremental Update:</b> <a href='{incremental.link}'>Here</a></p>"
        entry.description(description)
        return feed

    def generate(self):
        main_feed_generator = FeedGenerator()
        main_feed_generator.title('MIUI Updates Tracker by XiaomiFirmwareUpdater')
        main_feed_generator.link(href=website, rel='alternate')
        main_feed_generator.description('Your best website to track MIUI ROM releases!')
        main_feed_generator.language('en')
        main_feed_generator.logo(f'{website}/images/xfu.png')
        main_feed_generator.lastBuildDate(None)
        for update in self.updates:
            short_codename = update.codename.split('_')[0]
            if short_codename not in self.feeds.keys():
                feed_generator = FeedGenerator()
                feed_generator.title(f'{update.name} MIUI Updates Tracker by XiaomiFirmwareUpdater')
                feed_generator.link(href=f'{website}/miui/{short_codename}', rel='alternate')
                feed_generator.description('Your best website to track MIUI ROM releases!')
                feed_generator.language('en')
                feed_generator.logo(f'{website}/images/xfu.png')
                feed_generator.lastBuildDate(None)
            else:
                feed_generator = self.feeds.get(short_codename)
            feed_generator = self.add_feed_entry(feed_generator, update)
            self.feeds.update({short_codename: feed_generator})
            main_feed_generator = self.add_feed_entry(main_feed_generator, update)
        main_feed_generator.rss_file(f"{CONF_DIR}/rss/latest.xml")
        for codename, feed in self.feeds.items():
            feed.rss_file(f"{CONF_DIR}/rss/{codename}.xml")


async def main():
    all_updates = get_all_latest_updates()
    rss = RSSGenerator(all_updates)
    rss.generate()


def run():
    """asyncio trigger function"""
    event_loop = asyncio.get_event_loop()
    event_loop.run_until_complete(main())


if __name__ == '__main__':
    run()
