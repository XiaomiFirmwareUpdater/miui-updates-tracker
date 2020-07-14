"""
MIUI Websites Scraper class implementation
"""
from asyncio import sleep

from miui_updates_tracker.official.api_client.china_website import ChinaAPIClient
from miui_updates_tracker.official.api_client.global_website import GlobalAPIClient


class APIClient:
    """
    Xiaomi Websites API client / Scraper wrapper
    """

    def __init__(self):
        """
        Website Class constructor
        """
        self.global_website = GlobalAPIClient()
        self.china_website = ChinaAPIClient()

    async def get_updates(self, device):
        await sleep(5)
        if device.region == "China":
            return await self.china_website.get_updates(device.mi_website_id)
        else:
            return await self.global_website.get_updates(device.mi_website_id)

    async def get_fastboot_updates(self, device):
        await sleep(5)
        if device.region == "China":
            return await self.china_website.get_fastboot_updates(device.codename)
        else:
            return await self.global_website.get_fastboot_updates(device.codename)

    async def close(self):
        await self.china_website.close()
        await self.global_website.close()
