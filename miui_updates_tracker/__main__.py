"""MIUI Updates Tracker entry point"""
from importlib import import_module

from miui_updates_tracker import CONFIG
from miui_updates_tracker.common.database import close_db
from miui_updates_tracker.social.poster import generate_rss_feed
from miui_updates_tracker.tracker_official import run as official
from miui_updates_tracker.utils.export import export_data
from miui_updates_tracker.utils.git import git_commit_push

source = CONFIG.get('source')
extra_run = None
if source == "tracker_updater":
    from miui_updates_tracker.updater.tracker_updater import run as extra_run
elif source == "tracker_official":
    pass
else:
    try:
        script = import_module(f"{__package__}.{source}")
        extra_run = script.run()
    except ImportError:
        raise Exception("Incorrect source has been specified! exiting...")

if __name__ == '__main__':
    if extra_run:
        extra_run()
    official()
    export_data()
    generate_rss_feed()
    git_commit_push()
    close_db()
