import json
import logging
import re
from typing import List, Optional

from aiohttp import ClientResponse, ServerDisconnectedError
from bs4 import BeautifulSoup, Tag

from miui_updates_tracker.common.api_client.common_client import CommonClient
from miui_updates_tracker.common.database.database import (
    update_in_db,
    add_to_db,
    get_codename,
)
from miui_updates_tracker.common.database.models.miui_update import Update
from miui_updates_tracker.official.models.device import ChinaDevice
from miui_updates_tracker.utils.rom_file_parser import (
    rom_info_from_file,
    fastboot_info_from_file,
)
from miui_updates_tracker.utils.rom_utils import (
    get_rom_type,
    get_rom_branch,
    get_region_code_from_codename,
)

china_website_useragent = (
    "'Mozilla/5.0 (Linux; U; Android 10; zh-cn; M2007J1SC Build/QKQ1.200419.002) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/71.0.3578.141 "
    "Mobile Safari/537.36 XiaoMi/MiuiBrowser/12.8.25'"
)


class ChinaAPIClient(CommonClient):
    """
    Xiaomi Community website API client

    This class is used to get data from Xiaomi China website.
    :attr: `headers`: dict - HTTP request headers
    :meth: `get_devices` - Get all available devices on the website.
    :meth: `get_fastboot_devices` - Get all available fastboot devices on the website.
    :meth: `get_updates` - Get latest updates available for a device.
    :meth: `get_fastboot_updates` - Get latest fastboot update for a device.
    """

    def __init__(self):
        """
        Website Class constructor
        """
        super().__init__()
        self.base_url: str = (
            "https://api.vip.miui.com/api/community/post/detail?postId="
        )
        self._logger = logging.getLogger(__name__)
        self.fastboot_devices = []

    async def get_devices(self):
        """
        Get all available devices from the website.
        """
        response: ClientResponse
        async with self.session.get(f"{self.base_url}/download.html") as response:
            if response.status != 200:
                return
            page = BeautifulSoup(await response.text(), "html.parser")
            data = (
                [str(i) for i in page.select("script") if "var phones" in str(i)][0]
                .split("=")[1]
                .split(";")[0]
            )
            info = json.loads(data)
            self.devices = [ChinaDevice.from_response(item) for item in info]
            return self.devices

    async def get_fastboot_devices(self):
        """
        Get all available fastboot devices from the website.
        """
        response: ClientResponse
        async with self.session.get(
                f"{self.base_url}/shuaji-393.html",
                headers={"User-Agent": china_website_useragent},
        ) as response:
            if response.status != 200:
                return
            page = BeautifulSoup(await response.text(), "html.parser")
            links = page.select('a[href^="//update.miui.com/updates/"]')
            item: Tag
            for item in links:
                data = re.search(
                    r"\?d=(\w+)&b=(\w)&r=(\w+)?&n=(\w+)?", item.get("href")
                )
                self.fastboot_devices.append(
                    {
                        "device": re.search(r"(.*) ?最新", item.text)
                        .group(1)
                        .strip(),
                        "codename": data.group(1),
                        "branch": data.group(2),
                        "region": data.group(3),
                        "carrier": data.group(4),
                    }
                )
            return self.fastboot_devices

    async def get_updates(self, device_id: str) -> list:
        """
        Get the latest available updates for a device from the website.
        :param device_id: Device ID on the website
        :return: a list of the device's available updates information
        """
        # Get latest
        updates = []
        update = await self._fetch(device_id)
        if update:
            for item in update:
                updates.append(item)
        return updates

    async def _fetch(self, device_id: str) -> List[Update]:
        """
        Fetch an update and add it to the database if new
        :param device_id: device ID
        :return: Update object
        """
        updates = []
        links: List[str] = await self._request(device_id)
        if not links:
            return updates
        for item in links:
            filename = item.split("/")[-1]
            if update_in_db(filename):
                continue
            update = self._get_update(filename)
            if update:
                add_to_db(update)
                self._logger.info(f"Added {filename} to db")
                updates.append(update)
        return updates

    async def _request(self, device_id: str) -> list:
        """
        Perform an OTA request
        :param device_id: Miui China website device code
        :return: list of links
        """
        async with self.session.get(
                f"{self.base_url}{device_id}", headers={"Connection": "keep-alive"}
        ) as response:
            if response.status != 200:
                return []
            page_json = json.loads(await response.text())
            if page_json["code"] != 200:
                return []
            page_content = json.loads(page_json["entity"]["textContent"])
            links = []
            for content in page_content:
                if content["type"] != "txt":
                    continue
                for link_el in BeautifulSoup(content["txt"], "html.parser").select(
                        'a[href$=".zip"]'
                ):
                    link = link_el.get("href")
                    if "miui_" in link and not link.endswith("MiFlash2018-5-28-0.zip"):
                        links.append(link)
            return links

    def _get_update(self, filename: str) -> Optional[Update]:
        """
        Parse the response from th API into an Update object
        :param filename: update zip filename
        :return: Update object
        """
        info = rom_info_from_file(filename, more_details=True)
        codename = get_codename(info.get("miui_name")) if info.get("miui_name") else info.get("codename")
        if not codename:
            self._logger.warning(f"Can't find codename of {filename}!")
            return None
        version = info.get("version")
        return Update(
            codename=codename,
            version=version,
            android=info.get("android"),
            branch=get_rom_branch(version),
            type=get_rom_type(filename),
            method="Recovery",
            size=info.get("size"),
            link=info.get("link"),
            filename=filename,
            date=info.get("date"),
        )

    async def get_fastboot_updates(self, codename) -> list:
        """
        Get the latest available updates for a device from the website API.
        :param codename: Device codename
        :return:a list of the device's available updates information
        """
        updates = []
        update = await self._fetch_fastboot(codename)
        if update:
            updates.append(update)
        return updates

    async def _fetch_fastboot(self, codename) -> Optional[Update]:
        """
        Fetch an update and add it to the database if new
        :param codename: device codename
        :return: Update object
        """
        try:
            url: str = await self._request_fastboot(codename)
        except ServerDisconnectedError:
            return
        if not url:
            return
        filename = url.split("/")[-1]
        if update_in_db(filename):
            return
        update = self._get_fastboot_update(filename)
        if update:
            add_to_db(update)
            self._logger.info(f"Added {filename} to db")
        return update

    async def _request_fastboot(self, codename) -> str:
        """
        Perform a fastboot request
        :param codename: device codename
        :return: download URL
        """
        region = get_region_code_from_codename(codename)
        headers = {"Referer": "http://www.miui.com/"}
        async with self.session.head(
                f"https://update.miui.com/updates/v1/fullromdownload.php?d={codename}&b=F&r={region}&n=",
                headers=headers,
        ) as response:
            url = response.headers.get("Location")
            return url if url != "http://www.miui.com/" else None

    @staticmethod
    def _get_fastboot_update(filename) -> Update:
        """
        Parse the response from th API into an Update object
        :param filename: fastboot update filename
        :return: Update object
        """
        info = fastboot_info_from_file(filename, more_details=True)
        version = info.get("version")
        return Update(
            codename=info.get("codename"),
            version=version,
            android=info.get("android"),
            branch=get_rom_branch(version),
            type=get_rom_type(filename),
            method="Fastboot",
            size=info.get("size"),
            link=info.get("link"),
            filename=filename,
            date=info.get("date"),
        )
