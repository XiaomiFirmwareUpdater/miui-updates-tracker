""" MIUI Uodates Tracker utils """
import yaml


def is_roll_back(update: dict):
    """
    check if the new update is actually a rollback one
    """
    codename = update['codename']
    version = update['version']
    filename = update['filename']
    branch = get_branch(version)
    rom_type = get_type(filename).lower()
    try:
        with open(f'archive/{branch}_{rom_type}/{codename}.yml', 'r') as yaml_file:
            data = yaml.load(yaml_file, Loader=yaml.CLoader)
            versions = list(data[codename].keys())
        return bool(version in versions)
    except FileNotFoundError:
        return False


def get_branch(version: str) -> str:
    """ Get the branch of an update """
    return 'stable' if version.startswith('V') else 'weekly'


def get_region(filename, codename, version):
    """ Get the region of an update """
    if 'eea_global' in filename or 'eea_global' in codename or 'EU' in version:
        region = 'EEA'
    elif 'id_global' in filename or 'id_global' in codename or 'ID' in version:
        region = 'Indonesia'
    elif 'in_global' in filename or 'in_global' in codename or 'IN' in version:
        region = 'India'
    elif 'ru_global' in filename or 'ru_global' in codename or 'RU' in version:
        region = 'Russia'
    elif 'global' in filename or 'global' in codename or 'MI' in version:
        region = 'Global'
    else:
        region = 'China'
    return region


def get_type(filename):
    """ Get the type of an update """
    return 'Recovery' if '.tgz' in filename else 'Fastboot'
