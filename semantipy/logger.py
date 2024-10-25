from __future__ import annotations

import logging
import sys
from pathlib import Path

import colorlog

_logger_init = False
_file_handlers: dict[Path, logging.FileHandler] = {}

# These levels are between debug and info.
LOGGING_PROMPT = 15
LOGGING_RESPONSE = 16
logging.addLevelName(LOGGING_PROMPT, "PROMPT")
logging.addLevelName(LOGGING_RESPONSE, "RESPONSE")

_logger = logging.getLogger(__name__)


def init_python_logger() -> None:
    """
    Initialize the logger. Log to stdout by default.
    """
    global _logger_init
    if _logger_init:
        return

    logger = logging.getLogger("semantipy")
    logger.setLevel(level=logging.INFO)
    add_python_logging_handler(logger)

    _logger_init = True


def add_python_logging_handler(logger: logging.Logger, file: Path | None = None) -> logging.Handler:
    """
    Add a logging handler.
    If ``file`` is specified, log to file.
    Otherwise, add a handler to stdout.
    """
    fmt = "%(log_color)s[%(asctime)s] %(levelname)s (%(name)s) %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"

    formatter = colorlog.ColoredFormatter(
        fmt,
        datefmt,
        log_colors={
            "DEBUG": "cyan",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "red,bg_white",
            "PROMPT": "blue",
            "RESPONSE": "purple",
        },
    )

    if file is None:
        # Log to stdout.
        handler = logging.StreamHandler(sys.stdout)
    elif file in _file_handlers:
        # Log to file.
        # Reuse the existing handler.
        handler = _file_handlers[file]
    else:
        handler = logging.FileHandler(file)
        _file_handlers[file] = handler
    handler.setLevel(level=logging.DEBUG)  # Print all the logs.
    handler.setFormatter(formatter)

    logger.addHandler(handler)

    return handler
