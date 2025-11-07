"""
Logger utility for the application.

Provides centralized logging configuration with support for:
- Console and file logging
- Different log levels per handler
- Structured log formatting
- Rotation of log files
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional


class LoggerSetup:
    """Centralized logger configuration."""

    _loggers = {}

    @staticmethod
    def get_logger(
        name: str,
        level: int = logging.INFO,
        log_file: Optional[str] = None,
        max_bytes: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5,
        console_output: bool = True,
    ) -> logging.Logger:
        """
        Get or create a logger with the specified configuration.

        Args:
            name: Name of the logger (typically __name__ of the module)
            level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file: Optional path to log file. If None, only console logging is used
            max_bytes: Maximum size of log file before rotation (default: 10MB)
            backup_count: Number of backup files to keep (default: 5)
            console_output: Whether to output logs to console (default: True)

        Returns:
            Configured logger instance
        """
        # Return existing logger if already configured
        if name in LoggerSetup._loggers:
            return LoggerSetup._loggers[name]

        logger = logging.getLogger(name)
        logger.setLevel(level)
        logger.propagate = False

        # Clear any existing handlers
        logger.handlers.clear()

        # Create formatter
        formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # Add console handler
        if console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(level)
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)

        # Add file handler with rotation
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=max_bytes,
                backupCount=backup_count,
            )
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        # Cache the logger
        LoggerSetup._loggers[name] = logger

        return logger

    @staticmethod
    def get_uvicorn_logger(name: str = "uvicorn") -> logging.Logger:
        """
        Get logger configured for Uvicorn/FastAPI applications.

        Args:
            name: Logger name (default: "uvicorn")

        Returns:
            Configured logger instance
        """
        return LoggerSetup.get_logger(
            name=name,
            level=logging.INFO,
            log_file="logs/app.log",
            console_output=True,
        )


def get_logger(
    name: str,
    level: int = logging.INFO,
    log_file: Optional[str] = None,
) -> logging.Logger:
    """
    Convenience function to get a logger.

    Args:
        name: Name of the logger (typically __name__ of the module)
        level: Logging level (default: INFO)
        log_file: Optional path to log file

    Returns:
        Configured logger instance

    Example:
        >>> from app.utils.logger import get_logger
        >>> logger = get_logger(__name__)
        >>> logger.info("Application started")
        >>> logger.error("An error occurred", exc_info=True)
    """
    return LoggerSetup.get_logger(name=name, level=level, log_file=log_file)


# Default application logger
app_logger = get_logger("app", log_file="logs/app.log")
