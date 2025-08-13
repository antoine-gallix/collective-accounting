from loguru import logger
import sys

logger.remove()
logger.add(sys.stdout, format="{message}")
