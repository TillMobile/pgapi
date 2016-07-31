# Set default logging handler to avoid "No handler found" warnings.
import logging
import sys
import settings

LOG_LEVEL_INFO = "INFO"
LOG_LEVEL_DEBUG = "DEBUG"

try:  # Python 2.7+
    from logging import NullHandler
except ImportError:
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass

logging.getLogger(__name__).addHandler(NullHandler())

api = logging.getLogger()
api.setLevel(logging.DEBUG)

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter(
	'[%(asctime)s] [%(process)d] [HTTPSQL/%(levelname)s] %(message)s',
	datefmt="%Y-%m-%d %H:%M:%S %z"
)
ch.setFormatter(formatter)

api.addHandler(ch)

def info(msg):
	if settings.API_LOG_LEVEL in (LOG_LEVEL_INFO, LOG_LEVEL_DEBUG):
		api.info(msg)

def debug(msg):
	if settings.API_LOG_LEVEL == LOG_LEVEL_DEBUG:
		api.debug(msg)

def error(msg):
	api.error(msg)

info("Logging Initialized")