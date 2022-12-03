from miui_updates_tracker import CONFIG
from miui_updates_tracker.common.database.database import get_all_latest_updates
from miui_updates_tracker.social.discord_sender import DiscordBot
from miui_updates_tracker.social.facebook_page import FacebookPage
from miui_updates_tracker.social.rss import RSSGenerator
from miui_updates_tracker.social.telegram import TelegramBot
from miui_updates_tracker.social.twitter import TwitterBot
from miui_updates_tracker.social.xda import XDAPoster


async def post_updates(new_updates):
    # Telegram
    tg_config = CONFIG.get('telegram')
    if None not in tg_config.values():
        bot: TelegramBot = TelegramBot(tg_config.get('bot_token'), tg_config.get('chat'), "updater")
        await bot.post_updates(new_updates)
    # Discord
    discord_config = CONFIG.get('discord')
    if None not in discord_config.values():
        discord_bot = DiscordBot(discord_config.get('bot_token'))
        await discord_bot.post_updates(new_updates)
    # Twitter
    twitter_config: dict = CONFIG.get('twitter')
    if None not in twitter_config.values():
        twitter_bot = TwitterBot(twitter_config)
        await twitter_bot.post_updates(new_updates)
    # Facebook
    facebook_config: dict = CONFIG.get('facebook')
    if None not in facebook_config.values():
        facebook_page = FacebookPage(facebook_config.get('page_id'), facebook_config.get('page_token'))
        await facebook_page.post_updates(new_updates)
    # XDA
    xda_config = CONFIG.get('xda')
    if None not in xda_config.values():
        xda: XDAPoster = XDAPoster(xda_config.get('access_token'))
        await xda.post_updates(new_updates)


def generate_rss_feed():
    # RSS
    updates = get_all_latest_updates()
    rss = RSSGenerator(updates)
    rss.generate()

# updates = [Update(codename='merlin_in_global', version='V11.0.2.0.QJOINXM', android='10.0', branch='Stable',
#                   type='Full', method='Fastboot', size='2851806192', md5='ccbdaddff3da08fc7ca548c75448fc75',
#                   link='https://bigota.d.miui.com/V11.0.2.0.QJOINXM/'
#                        'merlin_in_global_images_V11.0.2.0.QJOINXM_20200624.0000.00_10.0_in_ccbdaddff3.tgz',
#                   changelog='Bug fixes and system optimizations', date='2020-06-24'),
#            Update(codename='jasmine_global', version='V11.0.11.0.QDIMIXM', android='10.0', branch='Stable',
#                   type='Full', method='Recovery', size='2851806192', md5='a1fbe5d37e2f4e95cbcd81a22e38d95a',
#                   link='https://bigota.d.miui.com/V11.0.11.0.QDIMIXM/'
#                        'miui_JASMINEGlobal_V11.0.11.0.QDIMIXM_a1fbe5d37e_10.0.zip',
#                   changelog='Bug fixes and system optimizations', date='2020-06-24'),
#            Update(
#                codename="lancelot", version="V11.0.4.0.QJCCNXM", android="10.0",
#                branch="Stable", method="Recovery", size="2040109465",
#                md5="89fd8abc76de4e216635e0cf29c15aed", filename="miui_LANCELOT_V11.0.4.0.QJCCNXM_89fd8abc76_10.0.zip",
#                link="https://bigota.d.miui.com/V11.0.4.0.QJCCNXM/miui_LANCELOT_V11.0.4.0.QJCCNXM_89fd8abc76_10.0.zip",
#                changelog="[Other]\nOptimized system performance\nImproved system security and stability"
#            )]
