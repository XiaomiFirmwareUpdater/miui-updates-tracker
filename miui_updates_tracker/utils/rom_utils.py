from miui_updates_tracker.common.constants import android_one_devices


def get_rom_branch(version: str):
    return "Stable" if version[0].isalpha() else "Beta"


def get_rom_type(filename: str):
    return "Full" if "ota-" not in filename else "Incremental"


def get_rom_method(filename: str):
    return "Recovery" if filename.endswith('.zip') else "Fastboot"


def get_region_code_from_codename(codename):
    if codename in android_one_devices:
        return ""
    if codename.endswith('_eea_global'):
        region = "eea"
    elif codename.endswith('_in_global'):
        region = "in"
    elif codename.endswith('_global'):
        region = "global"
    else:
        region = "cn"
    return region
