"""
Logging configuration for the knowledge base application.

This module provides a centralized logging configuration that supports:
- File logging with rotation
- Console logging with colored output
- Different log levels for different environments
- Custom formatting
- Component-specific logging
"""

import os
import sys
import logging
import logging.handlers
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
from functools import lru_cache

# ANSI color codes for console output
COLORS = {
    'GREY': '\033[38;21m',
    'BLUE': '\033[34m',
    'YELLOW': '\033[33;21m',
    'RED': '\033[31;21m',
    'BOLD_RED': '\033[31;1m',
    'RESET': '\033[0m'
}

class ColoredFormatter(logging.Formatter):
    """Custom formatter for colored console output."""
    
    FORMATS = {
        logging.DEBUG: COLORS['GREY'] + '%(asctime)s - %(name)s - %(levelname)s - %(message)s' + COLORS['RESET'],
        logging.INFO: COLORS['BLUE'] + '%(asctime)s - %(name)s - %(levelname)s - %(message)s' + COLORS['RESET'],
        logging.WARNING: COLORS['YELLOW'] + '%(asctime)s - %(name)s - %(levelname)s - %(message)s' + COLORS['RESET'],
        logging.ERROR: COLORS['RED'] + '%(asctime)s - %(name)s - %(levelname)s - %(message)s' + COLORS['RESET'],
        logging.CRITICAL: COLORS['BOLD_RED'] + '%(asctime)s - %(name)s - %(levelname)s - %(message)s' + COLORS['RESET']
    }
    
    def format(self, record: logging.LogRecord) -> str:
        """Format the log record with appropriate color."""
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, datefmt='%Y-%m-%d %H:%M:%S')
        return formatter.format(record)

class ComponentLogger:
    """Logger wrapper for component-specific logging."""
    
    def __init__(self, logger: logging.Logger):
        self._logger = logger
    
    def debug(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log debug message with component context."""
        self._logger.debug(msg, *args, **kwargs)
    
    def info(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log info message with component context."""
        self._logger.info(msg, *args, **kwargs)
    
    def warning(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log warning message with component context."""
        self._logger.warning(msg, *args, **kwargs)
    
    def error(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log error message with component context."""
        self._logger.error(msg, *args, **kwargs)
    
    def critical(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log critical message with component context."""
        self._logger.critical(msg, *args, **kwargs)
    
    def exception(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log exception with component context."""
        self._logger.exception(msg, *args, **kwargs)

@lru_cache(maxsize=None)
def get_logger(name: str = None) -> ComponentLogger:
    """Get a logger instance for a component.
    
    Args:
        name: Logger name (typically __name__ of the calling module)
        
    Returns:
        ComponentLogger instance
    """
    logger = logging.getLogger(name or 'knowledge_base')
    return ComponentLogger(logger)

def setup_file_logging(log_path: Path) -> logging.Handler:
    """Set up file logging with rotation.
    
    Args:
        log_path: Path to log directory
        
    Returns:
        Configured log handler
    """
    log_path.mkdir(parents=True, exist_ok=True)
    log_file = log_path / f"knowledge_base_{datetime.now():%Y%m%d}.log"
    
    handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10_000_000,  # 10MB
        backupCount=10,
        encoding='utf-8'
    )
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)
    return handler

def setup_console_logging() -> logging.Handler:
    """Set up console logging with colors.
    
    Returns:
        Configured log handler
    """
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(ColoredFormatter())
    return handler

def configure_logging(
    log_path: Optional[Path] = None,
    log_level: int = logging.INFO,
    enable_console: bool = True
) -> None:
    """Configure global logging settings.
    
    Args:
        log_path: Path to log directory (if None, file logging is disabled)
        log_level: Logging level to use
        enable_console: Whether to enable console logging
    """
    # Get root logger
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Add file handler if path is provided
    if log_path:
        logger.addHandler(setup_file_logging(log_path))
    
    # Add console handler if enabled
    if enable_console:
        logger.addHandler(setup_console_logging())
    
    # Set logging format for third-party loggers
    for name in logging.root.manager.loggerDict:
        if name.startswith('knowledge_base'):
            continue
        third_party_logger = logging.getLogger(name)
        third_party_logger.handlers = []
        third_party_logger.propagate = True

# Configure logging when module is imported
log_path = os.getenv('LOG_PATH')
log_level = getattr(logging, os.getenv('LOG_LEVEL', 'INFO'))
configure_logging(
    log_path=Path(log_path) if log_path else None,
    log_level=log_level,
    enable_console=True
)