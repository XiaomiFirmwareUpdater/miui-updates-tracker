from miui_updates_tracker import CONF_DIR
from miui_updates_tracker.common.database.helpers import export_latest, export_devices
from miui_updates_tracker.utils.data_manager import DataManager


def export_data():
    latest = export_latest()
    DataManager.write_file(f"{CONF_DIR}/data/latest.yml", latest)
    devices = export_devices()
    DataManager.write_file(f"{CONF_DIR}/data/devices.yml", devices)
