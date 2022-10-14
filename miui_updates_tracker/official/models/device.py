"""
Xiaomi Device representation class
"""
from dataclasses import dataclass


@dataclass
class GlobalDevice:
    """
    A class representing device information
    :param name: str - the name of the device
    :param id: str - the id of the device (on Mi Community website)
    :param image: str - the image of the device
    """
    name: str
    id: str
    image: str

    @classmethod
    def from_response(cls, response: dict):
        """
        Factory method to create an instance of :class:`Device` from Xiaomi updates api response
        :param response: dict - Xiaomi updates api response
        :return: :class:`Device` instance
        """
        return cls(response.get('name').strip(), response.get('id'),
                   response.get('pic_url'))

    def __str__(self):
        return f"{self.name} ({self.id})"


@dataclass
class ChinaDevice:
    """
    A class representing device information
    :param name: str - the name of the device
    :param id: str - the id of the device (on Mi Chinese website)
    :param image: str - the image of the device
    """
    name: str
    id: str
    image: str

    @classmethod
    def from_response(cls, response: dict):
        """
        Factory method to create an instance of :class:`Device` from Xiaomi updates api
        :param response: dict - Xiaomi updates api response
        :return: :class:`Device` instance
        """
        return cls(response.get('name').strip(), response.get('pid'),
                   response.get('pic'))

    def __str__(self):
        return f"{self.name} ({self.id})"
