from .Camps_data import Camps_data
import logging

# Init a basic logger in case a module isn't run from a driver
logging.getLogger('').handlers = []
level = logging.getLevelName('INFO')
logging.basicConfig(level=level)
