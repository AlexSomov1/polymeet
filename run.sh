#!/usr/bin/env bash
# Запуск PolyMeet одной командой. Нужны только Docker (с Compose v2) и bash.
set -euo pipefail

cd "$(dirname "$0")"

usage() {
    cat <<'EOF'
Использование: ./run.sh [команда]

  up      собрать и запустить систему, дождаться готовности (по умолчанию)
  down    остановить и удалить контейнеры (данные в томах сохраняются)
  logs    смотреть логи всех сервисов
EOF
}

command="${1:-up}"

case "$command" in
    up)
        docker compose up --build -d --wait
        port="${WEB_PORT:-80}"
        base="http://localhost"
        [ "$port" = "80" ] || base="$base:$port"
        echo
        echo "PolyMeet запущен: $base"
        echo "Документация API: $base/api/docs"
        ;;
    down)
        docker compose down
        ;;
    logs)
        docker compose logs -f
        ;;
    -h | --help | help)
        usage
        ;;
    *)
        echo "Неизвестная команда: $command" >&2
        usage >&2
        exit 1
        ;;
esac
