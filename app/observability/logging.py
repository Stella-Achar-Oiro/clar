import sys

from loguru import logger

from app.config import settings


def configure_logging() -> None:
    logger.remove()
    if settings.environment == "production":
        logger.add(sys.stdout, serialize=True, level=settings.log_level)
    else:
        logger.add(sys.stdout, level=settings.log_level, colorize=True)
