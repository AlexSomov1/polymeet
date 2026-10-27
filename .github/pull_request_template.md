Closes #

## Что сделано

-

## Как проверить

-

## Чек-лист

- [ ] Тесты написаны или обновлены, `pytest` / `npm test` проходят
- [ ] Линтеры чистые: `ruff check`, `ruff format --check`, `mypy` / `npm run lint`
- [ ] Если менялся API: обновлён `backend/openapi.json` (`python scripts/export_openapi.py`)
- [ ] Если менялся контракт (схемы, коды ответов): на PR стоит метка `api-change`, изменение описано выше
- [ ] Если добавлена миграция: номер ревизии следующий по цепочке, `downgrade` работает
