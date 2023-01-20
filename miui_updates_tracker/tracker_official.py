"""
MIUI Updates Tracker main module
This module is the entry point for the tracker script and contains the controller part
"""
import asyncio
import logging
from dataclasses import asdict

from miui_updates_tracker import CONF_DIR
from miui_updates_tracker.common.database.database import (
    get_mi_website_ids,
    get_fastboot_codenames,
)
from miui_updates_tracker.official.api_client.api_client import APIClient
from miui_updates_tracker.social.poster import post_updates
from miui_updates_tracker.utils.data_manager import DataManager
from miui_updates_tracker.utils.rom_utils import is_rom_working_link

logger = logging.getLogger(__name__)


async def check_update(device, api):
    """Asynchronously checks device updates"""
    updates: list = await api.get_updates(device)
    logger.debug(updates)
    return [i for i in updates] if updates else None


async def check_fastboot_update(device, api):
    """Asynchronously checks device updates"""
    updates: list = await api.get_fastboot_updates(device)
    logger.debug(updates)
    return [i for i in updates] if updates else None


async def main():
    """Main function"""
    new_updates: list = []
    devices = get_mi_website_ids()
    fastboot_devices = get_fastboot_codenames()
    api: APIClient = APIClient()
    # save devices data
    await api.global_website.get_devices()
    logger.debug(f"global devices: {api.global_website.devices}")
    DataManager.write_file(
        f"{CONF_DIR}/data/official/global/devices.yml",
        [asdict(i) for i in api.global_website.devices],
    )
    # await api.china_website.get_devices()
    # logger.debug(f"china devices: {api.china_website.devices}")
    # DataManager.write_file(
    #     f"{CONF_DIR}/data/official/china/devices.yml",
    #     sorted([asdict(i) for i in api.china_website.devices], key=lambda x: x['id'], reverse=True))
    await api.global_website.get_fastboot_devices()
    logger.debug(f"global fastboot devices: {api.global_website.fastboot_devices}")
    DataManager.write_file(
        f"{CONF_DIR}/data/official/global/fastboot_devices.yml",
        api.global_website.fastboot_devices,
    )
    # await api.china_website.get_fastboot_devices()
    # DataManager.write_file(
    #     f"{CONF_DIR}/data/official/china/fastboot_devices.yml", api.china_website.fastboot_devices)
    # check for updates
    semaphore = asyncio.Semaphore(3)
    tasks = [asyncio.ensure_future(check_update(device, api)) for device in devices] + [
        asyncio.ensure_future(check_fastboot_update(codename, api))
        for codename in fastboot_devices
    ]
    async with semaphore:
        results = await asyncio.gather(*tasks)
        for result in results:
            if result:
                for update in result:
                    new_updates.append(update)
        await api.close()
    if new_updates:
        logger.info(f"New updates: {new_updates}")
        await post_updates(list(filter(lambda x: is_rom_working_link(x.link), new_updates)))


def run():
    """asyncio trigger function"""
    event_loop = asyncio.get_event_loop()
    event_loop.run_until_complete(main())
