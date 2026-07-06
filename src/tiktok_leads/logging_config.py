"""Structured logging configuration."""

import logging.config
from pathlib import Path
from typing import Dict, Any


def get_logging_config(log_level: str = "INFO", log_file: str = "logs/scraper.log") -> Dict[str, Any]:
    """Get logging configuration dictionary."""
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                "datefmt": "%Y-%m-%dT%H:%M:%S",
            },
            "detailed": {
                "format": "%(asctime)s [%(levelname)s] %(name)s %(filename)s:%(lineno)d: %(message)s",
                "datefmt": "%Y-%m-%dT%H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": log_level,
                "formatter": "standard",
                "stream": "ext://sys.stdout",
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "DEBUG",
                "formatter": "detailed",
                "filename": str(log_path),
                "maxBytes": 10 * 1024 * 1024,  # 10 MB
                "backupCount": 5,
                "encoding": "utf-8",
            },
        },
        "loggers": {
            "": {
                "handlers": ["console", "file"],
                "level": log_level,
                "propagate": True,
            },
        },
    }


def setup_logging(log_level: str = "INFO", log_file: str = "logs/scraper.log") -> None:
    """Setup logging configuration."""
    config = get_logging_config(log_level, log_file)
    logging.config.dictConfig(config)
