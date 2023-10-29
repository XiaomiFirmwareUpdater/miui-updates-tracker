"""Telegram Bot implementation"""
import logging
from asyncio import sleep
from base64 import b64encode
from typing import List, Union
from urllib.parse import quote

from humanize import naturalsize
from miui_updates_tracker.common.constants import website
from miui_updates_tracker.common.database.database import get_full_name, get_incremental
from miui_updates_tracker.common.database.models.miui_update import Update
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.error import BadRequest, RetryAfter
from telegram.ext import Application


class TelegramBot:
    """
    This class implements telegram bot that is used for sending updates to a telegram chat
    :attr:`updater` Telegram updater object
    :attr:`chat` Telegram chat username or id
    """

    def __init__(self, bot_token: str, chat: Union[int, str], source: str):
        """
        TelegramBot class constructor
        :param bot_token: Telegram Bot API access token
        :param chat: Telegram chat username or id that will be used to send updates to
        """
        self.application = Application.builder().token(bot_token).build()
        self.chat = chat if isinstance(chat, int) else f"@{chat}"
        self.source = source
        self._logger = logging.getLogger(__name__)

    async def post_updates(self, new_updates: List[Update]):
        """
        Send updates to a Telegram chat
        :param new_updates: a list of updates
        :return: None
        """
        for update in new_updates:
            message, button = self.generate_message(update)
            try:
                await self.send_telegram_message(message, button)
            except BadRequest:
                self._logger.warning(
                    f"Can't send telegram message of update {update}.\n Message:{message}"
                )

    def generate_message(self, update: Update) -> (str, InlineKeyboardMarkup):
        """
        Generate an update message from and `Update` object
        :param update: an Update object that contains update's information from official website
        :return: A string containing the update's message
         and inline keyboard that has download link'
        """
        message: str = ""
        is_hyperos = bool(update.version.startswith("OS"))
        if is_hyperos:
            message += f"#HyperOS\n"
        message += f"New update available!"
        short_codename = update.codename.split("_")[0]
        if update.method == "Fastboot":
            message += "\n"
        else:
            if self.source == "website":
                message += " (on the official website)\n"
            elif self.source == "updater":
                message += " (via OTA)\n"
            else:
                message += "\n"
        message += (
            f"*Device*: {get_full_name(update.codename)}\n"
            f"*Codename*: #{short_codename}\n"
            f"*Type*: {update.branch} {update.method}\n"
            f"*Version*: `{update.version} | {update.android}`\n"
            f"*Size*: {naturalsize(update.size)}\n"
        )
        if update.md5:
            message += f"*MD5*: `{update.md5}`\n"
        if update.changelog != "Bug fixes and system optimizations.":
            if len(update.changelog) + len(message) > 4000:
                branch = quote(update.branch.lower())
                message += (
                    f"*Changelog*: [Here]({website}/miui/{short_codename}/"
                    f"{branch}/{update.version}/)\n"
                )
            else:
                message += f"*Changelog*:\n`{update.changelog.replace('[', '(').replace(']', ')')}`\n"
        message += "\n@MIUIUpdatesTracker | @XiaomiFirmwareUpdater"
        button: InlineKeyboardButton = InlineKeyboardButton("Full ROM", update.link)
        # bot subscribe
        subscribe_command = str(
            b64encode(bytes(f"/subscribe miui {short_codename}", encoding="utf-8")),
            encoding="utf-8",
        )
        more_buttons = [
            InlineKeyboardButton("Latest", f"{website}/miui/{short_codename}"),
            InlineKeyboardButton("Archive", f"{website}/archive/miui/{short_codename}"),
            InlineKeyboardButton(
                "Subscribe", f"https://t.me/XiaomiGeeksBot?start={subscribe_command}"
            ),
        ]
        # incremental update
        if update.method == "Recovery":
            incremental = get_incremental(update.version)
            if incremental:
                incremental_button: InlineKeyboardButton = InlineKeyboardButton(
                    "Incremental", incremental.link
                )
                return message, InlineKeyboardMarkup(
                    [[button, incremental_button], more_buttons]
                )
        return message, InlineKeyboardMarkup([[button], more_buttons])

    async def send_telegram_message(
            self, message: str, reply_markup: InlineKeyboardMarkup
    ):
        """
        Send a message to Telegram chat
        :param message: A string of the update message to be sent
        :param reply_markup: A inline keyboard markup object that contains the update list
        :return:
        """
        try:
            await self.application.bot.send_message(
                chat_id=self.chat,
                text=message,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview="yes",
                reply_markup=reply_markup,
            )
        except RetryAfter as error:
            await sleep(error.retry_after)
            return await self.send_telegram_message(message, reply_markup)
        await sleep(3)
