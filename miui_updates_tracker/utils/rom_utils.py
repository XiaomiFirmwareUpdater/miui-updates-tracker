from requests import head


def get_rom_branch(version: str) -> str:
    if version[0].isalpha() and not version.endswith("DEV"):
        return "Stable"
    elif version.endswith("DEV"):
        return "Public Beta"
    else:
        return "Beta"


def get_rom_type(filename: str):
    return "Incremental" if ("ota-" in filename or "incremental-" in filename) else "Full"


def get_rom_method(filename: str):
    return "Recovery" if filename.endswith(".zip") else "Fastboot"


suffix_to_region = {
    "_eea_global": "eea",
    "_in_global": "in",
    "_in_rf_global": "in",
    "_id_global": "id",
    "_ru_global": "ru",
    "_tr_global": "tr",
    "_tw_global": "tw",
    "_jp_global": "jp",
    "_kr_global": "kr",
    "_global": "global",
}


def get_region_code_from_codename(codename):
    for suffix, region in suffix_to_region.items():
        if codename.endswith(suffix):
            return region
    return "cn"


def is_rom_working_link(rom_link: str) -> bool:
    head_response = head(rom_link)
    return bool(
        head_response.ok and int(head_response.headers.get("Content-Length", 0)) > 1024
    )
