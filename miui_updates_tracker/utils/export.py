from miui_updates_tracker import CONF_DIR
from miui_updates_tracker.common.database import session
from miui_updates_tracker.common.database.helpers import export_latest, export_devices
from miui_updates_tracker.common.database.models.miui_update import Update
from miui_updates_tracker.utils.data_manager import DataManager
from miui_updates_tracker.utils.rom_file_parser import get_headers


def repair_missing_sizes(batch_size: int = 200):
    updates = session.query(Update).filter(Update.size == None).order_by(Update.inserted_on.desc()).limit(batch_size).all()
    fixed = 0
    for update in updates:
        headers = get_headers(update.link)
        content_length = headers.get('Content-Length') if headers else None
        if content_length:
            update.size = int(content_length)
            fixed += 1
    if fixed:
        session.commit()
    return fixed


def export_data():
    repair_missing_sizes()
    latest = export_latest()
    DataManager.write_file(f"{CONF_DIR}/data/latest.yml", latest)
    devices = export_devices()
    DataManager.write_file(f"{CONF_DIR}/data/devices.yml", devices)
