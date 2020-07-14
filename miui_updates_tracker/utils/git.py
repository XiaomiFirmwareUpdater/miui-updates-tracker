"""
Git helper module
"""
import logging
from asyncio import create_subprocess_shell
from asyncio.subprocess import PIPE, Process
from datetime import datetime

from miui_updates_tracker import CONFIG, CONF_DIR


async def git_commit_push():
    """ Git helper function that adds, commits, and pushes changes"""
    command: str = f'git add {CONF_DIR}/data/official/*/*.yml ' \
                   f'{CONF_DIR}/data/*.yml -f {CONF_DIR}/rss/* && ' \
                   f'git -c "user.name=XiaomiFirmwareUpdater" -c "user.email=xiaomifirmwareupdater@gmail.com" ' \
                   f'commit -m "sync: {datetime.today().strftime("%d-%m-%Y %H:%M:%S")}" && ' \
                   f'git push -q https://{CONFIG.get("git_oauth_token")}@' \
                   f'github.com/XiaomiFirmwareUpdater/' \
                   f'miui-updates-tracker.git HEAD:master'
    process: Process = await create_subprocess_shell(command, stdin=PIPE, stdout=PIPE)
    await process.wait()
    if process.returncode != 0 and process.returncode != 1:
        stdout = await process.stdout.read()
        logger = logging.getLogger(__name__)
        logger.warning(f"Cannot commit and push changes! Error code: {process.returncode}\n"
                       f"Output: {stdout.decode()}")
