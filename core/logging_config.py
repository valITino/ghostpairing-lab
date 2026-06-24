"""
Structured logging configuration using loguru.
JSON-formatted logs with rotation, request ID propagation, and phone redaction.
Falls back to standard logging if loguru is not installed.
"""
import sys
import logging as stdlib_logging

try:
    from loguru import logger
    HAS_LOGURU = True
except ImportError:
    HAS_LOGURU = False
    logger = None

from config import (
    LOG_FILE,
    LOG_LEVEL,
    LOG_MAX_SIZE,
    LOG_RETENTION,
    LOG_FORMAT,
    LOG_PHONE_REDACTION,
)


def _phone_redaction_filter(record: dict) -> bool:
    """Redact phone numbers from log messages if enabled."""
    if LOG_PHONE_REDACTION and record.get("message"):
        import re

        msg = str(record["message"])
        # Replace phone numbers with truncated versions: +1234***
        msg = re.sub(r"(\+\d{4})\d+", r"\1***", msg)
        record["message"] = msg
    return True


def _setup_stdlib_logging():
    """Fallback: configure standard library logging when loguru is unavailable."""
    log = stdlib_logging.getLogger("ghostpairing")
    log.setLevel(getattr(stdlib_logging, LOG_LEVEL, stdlib_logging.INFO))

    if not log.handlers:
        handler = stdlib_logging.StreamHandler(sys.stdout)
        handler.setFormatter(stdlib_logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%H:%M:%S",
        ))
        log.addHandler(handler)

        # File handler
        try:
            fh = stdlib_logging.FileHandler(LOG_FILE)
            fh.setFormatter(stdlib_logging.Formatter(
                '{"timestamp":"%(asctime)s","level":"%(levelname)s",'
                '"logger":"%(name)s","message":"%(message)s"}',
                datefmt="%Y-%m-%dT%H:%M:%S",
            ))
            fh.setLevel(stdlib_logging.DEBUG)
            log.addHandler(fh)
        except Exception:
            pass

    return log


def setup_logging():
    """Configure structured logging. Call once at app startup."""
    if not HAS_LOGURU:
        return _setup_stdlib_logging()

    logger.remove()  # Remove default handler

    if LOG_FORMAT == "json":
        logger.add(
            sys.stdout,
            format=(
                '{{"timestamp":"{time:YYYY-MM-DDTHH:mm:ss.SSSZ}","level":"{level}",'
                '"logger":"{name}","message":"{message}","function":"{function}",'
                '"line":{line}}}'
            ),
            level=LOG_LEVEL,
            filter=_phone_redaction_filter,
            colorize=False,
        )
    else:
        logger.add(
            sys.stdout,
            format=(
                "<green>{time:HH:mm:ss}</green> | "
                "<level>{level: <8}</level> | "
                "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
                "<level>{message}</level>"
            ),
            level=LOG_LEVEL,
            filter=_phone_redaction_filter,
            colorize=True,
        )

    # File sink with rotation
    logger.add(
        LOG_FILE,
        format=(
            '{{"timestamp":"{time:YYYY-MM-DDTHH:mm:ss.SSSZ}","level":"{level}",'
            '"logger":"{name}","message":"{message}","function":"{function}",'
            '"line":{line}}}'
        ),
        level="DEBUG",
        rotation=LOG_MAX_SIZE,
        retention=LOG_RETENTION,
        compression="gz",
        filter=_phone_redaction_filter,
    )

    return logger


def get_logger(name: str = __name__):
    """Get a logger instance with the given name."""
    if HAS_LOGURU:
        return logger.bind(name=name)
    else:
        return stdlib_logging.getLogger(f"ghostpairing.{name}")
