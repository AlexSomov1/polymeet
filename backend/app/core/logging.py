"""Логирование: structlog, одна JSON-строка на событие в STDOUT.

Стандартный ``logging`` (uvicorn, gunicorn, arq, sqlalchemy) идёт через тот же
форматтер, поэтому в выводе нет строк в другом формате.
"""

import logging
import sys
from contextvars import ContextVar
from typing import Any

import structlog
from structlog.typing import Processor

# Поля строки http_request, которые проставляет обработка запроса (user_id, cache).
# Словарь изменяемый: он общий для middleware и зависимостей, даже если зависимость
# выполняется в пуле потоков с копией контекста.
_request_fields: ContextVar[dict[str, Any] | None] = ContextVar("request_fields", default=None)

_PROPAGATING_LOGGERS = ("uvicorn", "uvicorn.error", "gunicorn", "gunicorn.error", "arq")
_SILENCED_LOGGERS = ("uvicorn.access", "gunicorn.access", "sqlalchemy")


class StdoutHandler(logging.Handler):
    """Пишет в текущий ``sys.stdout`` (а не в тот, что был при создании)."""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            stream = sys.stdout
            stream.write(self.format(record) + "\n")
            stream.flush()
        except Exception:
            self.handleError(record)


def _shared_processors() -> list[Processor]:
    return [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso", utc=True, key="ts"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]


def json_formatter() -> logging.Formatter:
    """Форматтер для stdlib-записей; используется и в ``logconfig_dict`` gunicorn."""
    return structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=_shared_processors(),
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(ensure_ascii=False),
        ],
    )


def configure_logging(level: str = "INFO") -> None:
    """Настраивает structlog и stdlib logging. Повторный вызов безопасен."""
    log_level = logging.getLevelNamesMapping().get(level.upper(), logging.INFO)

    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            *_shared_processors(),
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    root = logging.getLogger()
    for handler in list(root.handlers):
        if isinstance(handler, StdoutHandler):
            root.removeHandler(handler)
    handler = StdoutHandler()
    handler.setFormatter(json_formatter())
    root.addHandler(handler)
    root.setLevel(log_level)

    for name in _PROPAGATING_LOGGERS:
        logger = logging.getLogger(name)
        logger.handlers.clear()
        logger.propagate = True
        logger.setLevel(logging.NOTSET)
    for name in _SILENCED_LOGGERS:
        logger = logging.getLogger(name)
        logger.handlers.clear()
        logger.propagate = True
        logger.setLevel(logging.WARNING)


def start_request_context(request_id: str) -> dict[str, Any]:
    """Начинает контекст логов запроса; возвращает словарь его полей."""
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(request_id=request_id)
    fields: dict[str, Any] = {}
    _request_fields.set(fields)
    return fields


def end_request_context() -> None:
    structlog.contextvars.clear_contextvars()
    _request_fields.set(None)


def bind_request_context(**fields: Any) -> None:
    """Добавляет поля в логи текущего запроса и в его итоговую строку http_request."""
    structlog.contextvars.bind_contextvars(**fields)
    current = _request_fields.get()
    if current is not None:
        current.update(fields)
