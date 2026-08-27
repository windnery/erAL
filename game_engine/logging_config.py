"""Crash-only logging for the game runtime.

The game used to write every successful command and save transition to a
runtime log. That produces a lot of noise and is not useful when a tester
reports a crash. This module deliberately keeps the logging surface small:
only an explicit crash report is written to disk.
"""

from __future__ import annotations

import json
import logging
import platform
import sys
import threading
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path
from types import TracebackType
from typing import Final


LOG_FILE_NAME = 'crash.log'
LOGGER_NAME = 'eral'
DEFAULT_LOG_DIR: Final = Path(__file__).resolve().parent.parent / 'logs'
_CRASH_EVENT = 'game.crashed'
_CRASH_LEVEL = logging.CRITICAL
_STANDARD_FIELDS: Final = frozenset(logging.makeLogRecord({}).__dict__) | {
    'asctime',
    'message',
}

_context = threading.local()
_hooks_lock = threading.Lock()
_hooks_installed = False
_previous_sys_excepthook = None
_previous_threading_excepthook = None
_reported_exceptions: dict[int, BaseException] = {}


def _limit_text(value: object, limit: int = 8_000) -> str:
    """Keep malformed client input from making a report unreasonably large."""

    text = str(value)
    if len(text) <= limit:
        return text
    return f'{text[:limit]}...'


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
            'runtime': {
                'python': platform.python_version(),
                'platform': platform.platform(),
            },
        }
        if record.exc_info is not None:
            error_type, error, _ = record.exc_info
            payload['exception'] = {
                'type': error_type.__name__ if error_type else 'UnknownError',
                'message': _limit_text(error),
                'traceback': self.formatException(record.exc_info),
            }
        return json.dumps(payload, ensure_ascii=False, default=str)


def set_runtime_context(**fields: object) -> None:
    """Store lightweight last-action context without writing an action log.

    Context is thread-local because pywebview may execute API calls on worker
    threads. It is included only if that thread subsequently crashes.
    """

    current = getattr(_context, 'fields', None)
    if current is None:
        current = {}
        _context.fields = current
    current.update(fields)


def clear_runtime_context() -> None:
    _context.fields = {}


def _get_runtime_context() -> dict[str, object]:
    return dict(getattr(_context, 'fields', {}))


def _mark_exception_reported(error: BaseException) -> bool:
    """Avoid duplicate records when an API boundary and thread hook see one error."""

    error_id = id(error)
    with _hooks_lock:
        if error_id in _reported_exceptions:
            return False
        _reported_exceptions[error_id] = error
        # This is only a safety valve for a long-running test session.
        if len(_reported_exceptions) > 1_024:
            _reported_exceptions.clear()
            _reported_exceptions[error_id] = error
    return True


def report_crash(
    error: BaseException,
    *,
    source: str,
    context: dict[str, object] | None = None,
    traceback: TracebackType | None = None,
) -> bool:
    """Write one structured crash record and return whether it was written.

    This function intentionally accepts an exception rather than a message so
    every backend report contains a real traceback. It is safe to call from an
    exception hook: failures in the reporting path are swallowed so they do
    not hide the original crash.
    """

    if isinstance(error, (KeyboardInterrupt, SystemExit)):
        return False
    if not _mark_exception_reported(error):
        return False

    report_context = _get_runtime_context()
    if context:
        report_context.update(context)
    try:
        logger = logging.getLogger(LOGGER_NAME)
        logger.critical(
            _CRASH_EVENT,
            exc_info=(type(error), error, traceback or error.__traceback__),
            extra={
                'source': source,
                'context': report_context,
            },
        )
        for handler in logger.handlers:
            handler.flush()
        return True
    except Exception:
        # The original exception must remain visible even if the disk is full
        # or a logging handler has become unavailable.
        return False


class FrontendError(RuntimeError):
    """A browser-side error represented as a normal structured exception."""


def report_frontend_error(
    message: object,
    *,
    source: object = '',
    line: object = None,
    column: object = None,
    stack: object = '',
) -> bool:
    """Persist an unhandled JavaScript error received from the webview."""

    error = FrontendError(_limit_text(message))
    return report_crash(
        error,
        source='frontend',
        context={
            'client_source': _limit_text(source),
            'line': line,
            'column': column,
            'javascript_stack': _limit_text(stack),
        },
    )


def _sys_excepthook(
    error_type: type[BaseException],
    error: BaseException,
    traceback: TracebackType | None,
) -> None:
    report_crash(error, source='sys.excepthook', traceback=traceback)
    if _previous_sys_excepthook is not None:
        _previous_sys_excepthook(error_type, error, traceback)


def _threading_excepthook(args: threading.ExceptHookArgs) -> None:
    report_crash(
        args.exc_value,
        source='threading.excepthook',
        traceback=args.exc_traceback,
    )
    if _previous_threading_excepthook is not None:
        _previous_threading_excepthook(args)


def _install_exception_hooks() -> None:
    global _hooks_installed, _previous_sys_excepthook, _previous_threading_excepthook
    with _hooks_lock:
        if _hooks_installed:
            return
        _previous_sys_excepthook = sys.excepthook
        sys.excepthook = _sys_excepthook
        if hasattr(threading, 'excepthook'):
            _previous_threading_excepthook = threading.excepthook
            threading.excepthook = _threading_excepthook
        _hooks_installed = True


def _restore_exception_hooks() -> None:
    global _hooks_installed, _previous_sys_excepthook, _previous_threading_excepthook
    with _hooks_lock:
        if not _hooks_installed:
            return
        if _previous_sys_excepthook is not None:
            sys.excepthook = _previous_sys_excepthook
        if hasattr(threading, 'excepthook') and _previous_threading_excepthook is not None:
            threading.excepthook = _previous_threading_excepthook
        _previous_sys_excepthook = None
        _previous_threading_excepthook = None
        _reported_exceptions.clear()
        _hooks_installed = False


def configure_logging(log_dir: Path | None = None) -> logging.Logger:
    """Configure crash-only logging and process/thread exception hooks."""

    shutdown_logging()
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(_CRASH_LEVEL)
    logger.propagate = False
    target_dir = Path(log_dir) if log_dir else DEFAULT_LOG_DIR
    try:
        target_dir.mkdir(parents=True, exist_ok=True)
        handler = RotatingFileHandler(
            target_dir / LOG_FILE_NAME,
            maxBytes=2_000_000,
            backupCount=3,
            encoding='utf-8',
            delay=True,
        )
        handler.setLevel(_CRASH_LEVEL)
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)
    except OSError:
        # There is no useful persistent destination in this case, but the
        # process hooks still capture the error for stderr/debugger output.
        fallback = logging.StreamHandler()
        fallback.setLevel(_CRASH_LEVEL)
        fallback.setFormatter(logging.Formatter('%(levelname)s %(name)s %(message)s'))
        logger.addHandler(fallback)
    _install_exception_hooks()
    return logger


def shutdown_logging() -> None:
    logger = logging.getLogger(LOGGER_NAME)
    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        handler.flush()
        handler.close()
    logger.setLevel(logging.NOTSET)
    _restore_exception_hooks()
    clear_runtime_context()
