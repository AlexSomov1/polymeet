import json
import re
import time
from typing import Any

import structlog
from starlette.datastructures import Headers, MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.errors import InternalError, error_body
from app.core.ids import new_id
from app.core.logging import end_request_context, start_request_context

REQUEST_ID_HEADER = "X-Request-ID"
_VALID_REQUEST_ID = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")

logger = structlog.get_logger(__name__)


class RequestContextMiddleware:
    """Request ID, контекст логов и одна строка ``http_request`` на каждый запрос.

    Необработанное исключение логируется как ``http_error`` с трассировкой, клиент
    получает 500 в стандартном формате без внутренних деталей.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        incoming = Headers(scope=scope).get(REQUEST_ID_HEADER)
        request_id = incoming if incoming and _VALID_REQUEST_ID.match(incoming) else new_id()
        fields = start_request_context(request_id)
        started = time.perf_counter()
        status = 500
        response_started = False

        async def send_with_request_id(message: Message) -> None:
            nonlocal status, response_started
            if message["type"] == "http.response.start":
                response_started = True
                status = message["status"]
                MutableHeaders(scope=message)[REQUEST_ID_HEADER] = request_id
            await send(message)

        try:
            await self.app(scope, receive, send_with_request_id)
        except Exception:
            logger.exception("http_error", method=scope["method"], path=_route_path(scope))
            if response_started:
                raise
            await _send_internal_error(send_with_request_id)
        finally:
            logger.info(
                "http_request",
                method=scope["method"],
                path=_route_path(scope),
                status=status,
                duration_ms=int((time.perf_counter() - started) * 1000),
                **fields,
            )
            end_request_context()


def _route_path(scope: Scope) -> str:
    """Шаблон маршрута (``/themes/{id}``), если роутер его определил, иначе путь."""
    route = scope.get("route")
    template = getattr(route, "path", None)
    return template if isinstance(template, str) else str(scope["path"])


async def _send_internal_error(send: Send) -> None:
    body = json.dumps(error_body(InternalError.code, InternalError.default_message)).encode()
    headers: list[tuple[bytes, bytes]] = [
        (b"content-type", b"application/json"),
        (b"content-length", str(len(body)).encode()),
    ]
    start: dict[str, Any] = {"type": "http.response.start", "status": 500, "headers": headers}
    await send(start)
    await send({"type": "http.response.body", "body": body})
