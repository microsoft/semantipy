from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any, TYPE_CHECKING

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


class TuningLogger:
    """Base class for logging the tuning process."""

    def on_candidate(self, instance: Any) -> None:
        pass

    def on_feedback(self, instance: Any, feedback: Any) -> None:
        pass

    def register_on(self, tuner: Tuner) -> None:
        tuner.register_candidate_callback(self.on_candidate)
        tuner.register_feedback_callback(self.on_feedback)


class ConsoleTuningLogger(TuningLogger):
    """A logger that logs the progress to the console."""

    def __init__(self) -> None:
        self.sample_counter = 0

    def on_candidate(self, instance: Any) -> None:
        self.sample_counter += 1
        config = _tunable_as_dict(instance)
        _logger.info("[Sample %d] %r", self.sample_counter, config)

    def on_feedback(self, instance: Any, feedback: Any) -> None:
        _logger.info(
            "[Feedback %d] %r: %r",
            self.sample_counter,
            _tunable_as_dict(instance),
            feedback,
        )


class WandbTuningLogger(TuningLogger):
    """A logger that sends the result to wandb."""

    def __init__(self, project: str) -> None:
        self.sample_counter = 0
        self.project = project

    def on_candidate(self, instance: Any) -> None:
        self.sample_counter += 1

    def on_metric(self, instance: Any, metrics: dict[str, Any]) -> None:
        import wandb

        # FIXME: this should be moved to on_sample?
        wandb.init(project=self.project, config=_tunable_as_dict(instance))
        wandb.log(metrics)

        wandb.finish()  # TODO: mark a instance as failed
