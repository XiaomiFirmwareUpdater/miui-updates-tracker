from requests import head

from miui_updates_tracker.common.constants import android_one_devices


def get_rom_branch(version: str) -> str:
    if version[0].isalpha() and not version.endswith("DEV"):
        return "Stable"
    elif version.endswith("DEV"):
        return "Public Beta"
    else:
        return "Beta"


def get_rom_type(filename: str):
    return "Full" if "ota-" not in filename else "Incremental"


def get_rom_method(filename: str):
    return "Recovery" if filename.endswith(".zip") else "Fastboot"


def get_region_code_from_codename(codename):
    if codename in android_one_devices:
        return ""
    if codename.endswith("_eea_global"):
        region = "eea"
    elif codename.endswith("_in_global") or codename.endswith("_in_rf_global"):
        region = "in"
    elif codename.endswith("_global"):
        region = "global"
    else:
        region = "cn"
    return region


def is_rom_working_link(rom_link: str) -> bool:
    head_response = head(rom_link)
    return bool(
        head_response.ok and int(head_response.headers.get("Content-Length", 0)) > 1024
    )
