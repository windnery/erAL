import json
import logging
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Final


LOG_FILE_NAME = 'eral.log'
LOGGER_NAME = 'eral'
DEFAULT_LOG_DIR: Final = Path(__file__).resolve().parent.parent / 'logs'
_STANDARD_FIELDS: Final = frozenset(logging.makeLogRecord({}).__dict__) | {
    'asctime',
    'message',
}


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        fields = {
            key: value
            for key, value in record.__dict__.items()
            if key not in _STANDARD_FIELDS and not key.startswith('_')
        }
        payload = {
            'timestamp': datetime.fromtimestamp(
                record.created,
                timezone.utc,
            ).astimezone().isoformat(timespec='milliseconds'),
            'level': record.levelname,
            'event': record.getMessage(),
            'logger': record.name,
            'fields': dict(sorted(fields.items())),
        }
        if record.exc_info is not None:
            error_type, error, _ = record.exc_info
            payload['exception'] = {
                'type': error_type.__name__,
                'message': str(error),
                'traceback': self.formatException(record.exc_info),
            }
        return json.dumps(payload, ensure_ascii=False, default=str)


def configure_logging(log_dir: Path | None = None) -> logging.Logger:
    shutdown_logging()
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    target_dir = log_dir or DEFAULT_LOG_DIR
    try:
        target_dir.mkdir(parents=True, exist_ok=True)
        handler = RotatingFileHandler(
            target_dir / LOG_FILE_NAME,
            maxBytes=2_000_000,
            backupCount=3,
            encoding='utf-8',
            delay=True,
        )
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)
    except OSError:
        fallback = logging.StreamHandler()
        fallback.setFormatter(logging.Formatter('%(levelname)s %(name)s %(message)s'))
        logger.addHandler(fallback)
        logger.warning('logging.file_unavailable', extra={'log_dir': str(target_dir)})
    return logger


def shutdown_logging() -> None:
    logger = logging.getLogger(LOGGER_NAME)
    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        handler.flush()
        handler.close()
