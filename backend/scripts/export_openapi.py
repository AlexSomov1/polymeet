"""Записывает OpenAPI-спецификацию приложения в backend/openapi.json.

Запуск из каталога backend: ``python scripts/export_openapi.py``.
"""

from pathlib import Path

from app.api.openapi import render_openapi
from app.main import create_app

OPENAPI_PATH = Path(__file__).resolve().parent.parent / "openapi.json"


def main() -> None:
    OPENAPI_PATH.write_text(render_openapi(create_app()), encoding="utf-8")


if __name__ == "__main__":
    main()
