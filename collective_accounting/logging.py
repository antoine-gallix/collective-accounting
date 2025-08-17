import sys

from loguru import logger

logger.remove()
logger.add(sys.stdout, format="<level>{message}</level>", colorize=True)
