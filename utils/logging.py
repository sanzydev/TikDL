import logging
import re
import sys
from typing import Optional

LOGGER_NAME = "tiktokdl"

SENSITIVE_PATTERNS = [
    (re.compile(r"(sessionid=)[^;&\s]+", re.IGNORECASE), r"\1[REDACTED]"),
    (re.compile(r"(tt_chain_token=)[^;&\s]+", re.IGNORECASE), r"\1[REDACTED]"),
    (re.compile(r"(signature=)[^;&\s]+", re.IGNORECASE), r"\1[REDACTED]"),
    (re.compile(r"(token=)[^;&\s]+", re.IGNORECASE), r"\1[REDACTED]"),
    (re.compile(r"(cookie:\s*)[^\r\n]+", re.IGNORECASE), r"\1[REDACTED]"),
    (re.compile(r"(set-cookie:\s*)[^\r\n]+", re.IGNORECASE), r"\1[REDACTED]"),
]


class RedactingFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        original = super().format(record)
        sanitized = original
        for pattern, replacement in SENSITIVE_PATTERNS:
            sanitized = pattern.sub(replacement, sanitized)
        return sanitized


def configure_logging(debug: bool = False, log_file: Optional[str] = None) -> logging.Logger:
    logger = logging.getLogger(LOGGER_NAME)
    level = logging.DEBUG if debug else logging.CRITICAL
    logger.setLevel(level)

    if logger.hasHandlers():
        logger.handlers.clear()

    formatter = RedactingFormatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    if debug:
        handler = logging.StreamHandler(sys.stderr)
        handler.setLevel(logging.DEBUG)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    else:
        logger.addHandler(logging.NullHandler())

    if log_file:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG if debug else logging.INFO)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(subname: Optional[str] = None) -> logging.Logger:
    name = f"{LOGGER_NAME}.{subname}" if subname else LOGGER_NAME
    return logging.getLogger(name)
