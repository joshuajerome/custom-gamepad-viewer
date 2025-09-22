from loguru import logger
import sys

def setup_logging(level: str = "INFO"):
    logger.remove()
    logger.add(
        sys.stderr,
        level=level.upper(),
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>",
    )
    return logger
