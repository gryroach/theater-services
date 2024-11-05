import logging
import sys
from logging.handlers import RotatingFileHandler

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler(stream=sys.stdout)
console_handler.setLevel(logging.WARNING)

rotating_handler = RotatingFileHandler(
    filename='app.log',
    maxBytes=256000,
    backupCount=5,
    encoding='utf-8',
)
rotating_handler.setLevel(logging.INFO)

formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(name)s: %(message)s'
)
console_handler.setFormatter(formatter)
rotating_handler.setFormatter(formatter)

logger.addHandler(rotating_handler)
logger.addHandler(console_handler)
