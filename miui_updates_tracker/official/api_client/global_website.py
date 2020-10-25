"""
MIUI Global Website API Client class implementation
"""
import json
import logging
import re
from typing import List, Optional, Dict

from aiohttp import ClientResponse
from miui_updates_tracker.common.api_client.common_client import CommonClient
from miui_updates_tracker.common.database.database import update_in_db, add_to_db, get_codename, update_stable_beta, \
    get_update_by_version
from miui_updates_tracker.common.database.models.miui_update import Update
from miui_updates_tracker.official.models.device import GlobalDevice
from miui_updates_tracker.utils.helpers import human_size_to_bytes
from miui_updates_tracker.utils.rom_file_parser import rom_info_from_file, fastboot_info_from_file
from miui_updates_tracker.utils.rom_utils import get_rom_branch, get_rom_type, get_rom_method, \
    get_region_code_from_codename


class GlobalAPIClient(CommonClient):
    """
    c.mi.com website API client

    This class is used to get data from Xiaomi Global website API.
    It's responsible for interacting with Xiaomi Global website API in order to:
    - Get devices list.
    - Get device's updates information
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
        self.base_url: str = "https://c.mi.com/oc"
        self.headers = {
            'pragma': 'no-cache',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'en-US,en;q=0.9',
            'accept': 'application/json, text/javascript, */*; q=0.01',
            'cache-control': 'no-cache',
            'authority': 'c.mi.com',
            'x-requested-with': 'XMLHttpRequest',
            'connection': 'keep-alive',
            'referer': 'https://c.mi.com/oc/miuidownload/',
        }
        self._logger = logging.getLogger(__name__)
        self.fastboot_devices = []

    async def get_devices(self):
        """
        Get all available devices list from the website API.
        """
        response: ClientResponse
        async with self.session.get(f'{self.base_url}/rom/getphonelist', headers=self.headers) as response:
            if response.status == 200:
                response: dict = await self._get_json_response(response)
                self.devices = [GlobalDevice.from_response(item) for item in
                                response['phone_data']['phone_list']]
                return self.devices

    async def get_fastboot_devices(self):
        response: ClientResponse
        async with self.session.get(f'{self.base_url}/rom/getlinepackagelist') as response:
            if response.status == 200:
                response: list = await self._get_json_response(response)
                for item in response:
                    data = re.search(r'\?d=(\w+)&b=(\w)&r=(\w+)?', item['package_url'])
                    self.fastboot_devices.append({
                        'id': item.get('id'),
                        'device': re.search(r'★ ?(.*) Latest', item.get('package_name')).group(1),
                        'codename': data.group(1),
                        'branch': data.group(2),
                        'region': data.group(3)
                    })
            return self.fastboot_devices

    async def get_updates(self, device_id: str) -> list:
        """
        Get the latest available updates for a device from the website API.
        :param device_id: Device ID on the website
        :return:a list of the device's available updates information
        """
        updates = []
        update = await self._fetch(device_id)
        if update:
            for item in update:
                updates.append(item)
        return updates

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

    async def _request(self, device_id: str) -> list:
        """
        Perform an OTA request
        :param device_id: Mi Community API device code
        :return: OTA response dictionary
        """
        headers = self.headers.copy()
        headers['Referer'] = f'{self.base_url}/miuidownload/detail?device={device_id}'
        async with self.session.get(f'{self.base_url}/rom/getdevicelist?phone_id={device_id}',
                                    headers=self.headers) as response:
            if response.status == 200:
                response = await self._get_json_response(response)
                response = response['device_data']['device_list']
                files = []
                for _, info in response.items():
                    for branch in ['stable_rom', 'developer_rom']:
                        if info.get(branch):
                            details = info.get(branch)
                            files.append({'version': details.get('version'),
                                          'link': details.get('rom_url'),
                                          'filename': details.get('rom_url').split('/')[-1],
                                          'size': details.get('size')})
                return files

    async def _request_fastboot(self, codename) -> str:
        """
        Perform a fastboot request
        :param codename: device codename
        :return: download URL
        """
        region = get_region_code_from_codename(codename)
        headers = self.headers.copy()
        headers['Referer'] = f'{self.base_url}/miuidownload/detail?guide=2'
        async with self.session.head(
                f'https://update.miui.com/updates/v1/fullromdownload.php?d={codename}&b=F&r={region}&n=',
                headers=self.headers) as response:
            url = response.headers.get('Location')
            return url if url != "http://www.miui.com/" else None

    async def _fetch(self, device_id: str) -> List[Update]:
        """
        Fetch an update and add it to the database if new
        :param device_id: device ID
        :return: Update object
        """
        response: List[Dict] = await self._request(device_id)
        if response:
            updates = []
            for item in response:
                filename = item['filename']
                if update_in_db(filename):
                    recovery_update = get_update_by_version(item['version'])
                    update_stable_beta(recovery_update)
                    continue
                update = self._get_update(item)
                if update:
                    if update.branch == "Stable" and not get_update_by_version(update.version, method="Fastboot"):
                        update.branch = "Stable Beta"
                    add_to_db(update)
                    self._logger.info(f"Added {filename} to db")
                    updates.append(update)
            return updates

    async def _fetch_fastboot(self, codename) -> Optional[Update]:
        """
        Fetch an update and add it to the database if new
        :param codename: device codename
        :return: Update object
        """
        url: str = await self._request_fastboot(codename)
        if url:
            filename = url.split('/')[-1]
            if update_in_db(filename):
                return
            update = self._get_fastboot_update(filename)
            if update:
                add_to_db(update)
                self._logger.info(f"Added {filename} to db")
                recovery_update = get_update_by_version(update.version)
                update_stable_beta(recovery_update)
            return update

    @staticmethod
    def _get_fastboot_update(filename) -> Update:
        """
        Parse the response from th API into an Update object
        :param filename: fastboot update filename
        :return: Update object
        """
        info = fastboot_info_from_file(filename, more_details=True)
        version = info.get('version')
        return Update(
            codename=info.get('codename'), version=version,
            android=info.get('android'), branch=get_rom_branch(version),
            type=get_rom_type(filename), method="Fastboot",
            size=info.get('size'), link=info.get('link'),
            filename=filename, date=info.get('date')
        )

    def _get_update(self, item: dict) -> Optional[Update]:
        """
        Parse the response from th API into an Update object
        :param item: dictionary of update information
        :return: Update object
        """
        filename = item['filename']
        method = get_rom_method(filename)
        if method == "Recovery":
            info = rom_info_from_file(filename, more_details=True)
            codename = get_codename(info.get('miui_name'))
        else:
            info = fastboot_info_from_file(filename, more_details=True)
            codename = info.get('codename')
        if not codename:
            self._logger.warning(f"Can't find codename of {filename}!")
            return None
        version = info.get('version')
        return Update(
            codename=codename, version=version,
            android=info.get('android'), branch=get_rom_branch(version),
            type=get_rom_type(filename), method=method,
            size=human_size_to_bytes(item.get('size')),
            link=info.get('link'), filename=filename,
            date=info.get('date')
        )

    @staticmethod
    async def _get_json_response(_response: ClientResponse):
        """
        Get a JSON response from the HTTP response
        :param _response: ClientResponse: The API response client object
        :return:
        """
        response: dict = json.loads(await _response.text())
        if response['errmsg'] == "Success" and response['errno'] == 0:
            return response['data']
