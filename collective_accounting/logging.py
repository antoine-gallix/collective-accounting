import os
import sys

from loguru import logger

logger.remove()
logger.add(
    sys.stdout,
    format="<level>{message}</level>",
    colorize=True,
    level=os.environ.get("LEVEL") or "INFO",
)
