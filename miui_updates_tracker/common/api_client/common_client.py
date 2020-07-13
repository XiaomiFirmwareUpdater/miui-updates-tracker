"""
Xiaomi Websites common API Client class implementation
"""

from aiohttp import ClientSession


class CommonClient:
    """
    Base API class class
    It's responsible for interacting with Xiaomi websites in order to:
    - Get devices list.
    - Get device's updates information
    :attr: `session`: ClientSession - aiohttp client session object
    :attr: `base_url`: str - Website base URL
    :attr: `devices`: list - list of devices available on the website
    """

    def __init__(self):
        """
        Website Class constructor
        :param region: Xiaomi website region
        """
        self.session: ClientSession = ClientSession()
        self.base_url: str = ""
        self.devices: list = []

    async def close(self):
        """
        Closes the connection of aiohttp client
        :return:
        """
        await self.session.close()
