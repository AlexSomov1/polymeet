"""Конфигурация gunicorn для API: ``gunicorn -c gunicorn.conf.py app.main:app``."""

import os

bind = "0.0.0.0:8000"
worker_class = "uvicorn.workers.UvicornWorker"
workers = int(os.environ.get("WEB_CONCURRENCY", "2"))
graceful_timeout = 30
keepalive = 5
# Управляющий сокет gunicornc не нужен: процессом управляет Docker
control_socket_disable = True

# Запросы логирует RequestContextMiddleware, access-лог gunicorn не нужен.
accesslog = None
loglevel = os.environ.get("LOG_LEVEL", "INFO").lower()

# Собственные логи gunicorn — в тот же JSON-формат, что и у приложения.
logconfig_dict = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"json": {"()": "app.core.logging.json_formatter"}},
    "handlers": {"stdout": {"class": "app.core.logging.StdoutHandler", "formatter": "json"}},
    "root": {"level": loglevel.upper(), "handlers": ["stdout"]},
    "loggers": {
        "gunicorn.error": {"level": loglevel.upper(), "handlers": [], "propagate": True},
        "gunicorn.access": {"level": "WARNING", "handlers": [], "propagate": True},
    },
}
