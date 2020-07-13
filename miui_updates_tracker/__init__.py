"""MIUI Updates Tracker initialization"""
import logging
from logging import Formatter
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from sys import stderr

# from sys import stdout
import yaml

WORK_DIR = Path(__file__).parent
CONF_DIR = Path(__file__).parent.parent

# read script configuration file
with open(CONF_DIR / 'config.yml', 'r') as f:
    CONFIG = yaml.load(f, Loader=yaml.FullLoader)

# set logging configuration
LOG_FILE = CONF_DIR / 'last_run.log'
LOG_FORMAT: str = '%(asctime)s [%(levelname)s] %(name)s [%(module)s.%(funcName)s:%(lineno)d]: ' \
                  '%(message)s'
FORMATTER: Formatter = logging.Formatter(LOG_FORMAT)
handler = TimedRotatingFileHandler(LOG_FILE, when="d", interval=1, backupCount=2)
logging.basicConfig(filename=LOG_FILE, filemode='a', format=LOG_FORMAT)
# OUT = logging.StreamHandler(stdout)
ERR = logging.StreamHandler(stderr)
# OUT.setFormatter(FORMATTER)
ERR.setFormatter(FORMATTER)
# OUT.setLevel(logging.DEBUG)
ERR.setLevel(logging.WARNING)
LOGGER = logging.getLogger()
# LOGGER.addHandler(OUT)
LOGGER.addHandler(ERR)
LOGGER.addHandler(handler)
LOGGER.setLevel(logging.INFO)
