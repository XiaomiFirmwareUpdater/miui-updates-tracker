"""MIUI Updates Tracker helper functions"""
import re
from datetime import datetime

from humanize import naturalsize

units = {"BYTES": 1, "B": 1, "KB": 2 ** 10, "MB": 2 ** 20, "M": 2 ** 20, "GB": 2 ** 30, "G": 2 ** 30}


def is_newer_datetime(old_datetime: str, new_datetime: str) -> bool:
    """
    Check if a datetime is newer than another
    :param new_datetime: A datetime in posix time format
    :param old_datetime: A datetime in posix time format
    """
    return bool(
        datetime.strptime(new_datetime, '%d-%m-%Y') >= datetime.strptime(old_datetime, '%d-%m-%Y')
    )


def human_size_to_bytes(size: str):
    # based on https://stackoverflow.com/a/42865957/2002471
    if size == 0:
        return int(float(size) * units['B'])
    if size.isnumeric():
        return float(size)

    size = size.upper()
    if not re.match(r' ', size):
        size = re.sub(r'([\d.]+)([KMGT]?B?)', r'\1 \2', size)
    number, unit = [string.strip() for string in size.split()]
    return int(float(number) * units[unit])


def safe_naturalsize(size):
    return naturalsize(size) if size is not None else 'Unknown'
