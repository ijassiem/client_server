#Setting the threshold of logger to DEBUG
NOTSET = 0
DEBUG = 10
INFO = 20
WARNING = 30
ERROR = 40
CRITICAL = 50

import logging


def init_logging(name=__name__, loglevel=logging.DEBUG):
    # setup/configure logging
    FORMAT = '%(asctime)s. ' + logging.BASIC_FORMAT
    DATE = '%d-%b-%y %H:%M:%S'
    # LOGLEVEL = logging.DEBUG
    logging.basicConfig(datefmt=DATE, level=loglevel, format=FORMAT)
    # logger = logging.getLogger(__name__)  # log name
    logger = logging.getLogger(name)  # log name
    # logger.setLevel(LOGLEVEL)  # setting log level
    return logger
