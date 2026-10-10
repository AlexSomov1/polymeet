"""Записывает OpenAPI-спецификацию приложения в backend/openapi.json.

Запуск из каталога backend: ``python scripts/export_openapi.py``.
"""

import json
from pathlib import Path

from app.main import create_app

OPENAPI_PATH = Path(__file__).resolve().parent.parent / "openapi.json"


def render_openapi() -> str:
    spec = create_app().openapi()
    return json.dumps(spec, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def main() -> None:
    OPENAPI_PATH.write_text(render_openapi(), encoding="utf-8")


if __name__ == "__main__":
    main()
