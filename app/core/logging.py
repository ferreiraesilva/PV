from loguru import logger

from app.core.config import get_settings


def configure_logging() -> None:
    """Configure structured logging with environment-aware settings."""
    settings = get_settings()
    logger.remove()
    logger.add(
        sink=lambda msg: print(msg, flush=True),
        level=settings.log_level.upper(),
        serialize=True,
        backtrace=False,
        diagnose=False,
    )


__all__ = ["configure_logging", "logger"]
