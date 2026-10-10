import base64
import json
from datetime import timedelta

import jwt
import pytest

from app.core.config import Settings
from app.core.errors import UnauthorizedError
from app.core.ids import new_id
from app.core.security import create_token, decode_token, hash_password, verify_password
from tests.conftest import make_settings


async def test_password_hash_matches_only_original_password(settings: Settings) -> None:
    password_hash = await hash_password("correct horse battery", settings=settings)

    assert password_hash.startswith("$argon2id$")
    assert await verify_password("correct horse battery", password_hash)
    assert not await verify_password("correct horse batterY", password_hash)


async def test_same_password_gets_different_salted_hashes(settings: Settings) -> None:
    first = await hash_password("same-password", settings=settings)
    second = await hash_password("same-password", settings=settings)

    assert first != second
    assert await verify_password("same-password", second)


async def test_malformed_hash_is_not_accepted() -> None:
    assert not await verify_password("anything", "not-an-argon2-hash")


def test_access_token_carries_subject_and_default_ttl(settings: Settings) -> None:
    sub = new_id()

    first = decode_token(
        create_token(sub, "access", settings=settings), "access", settings=settings
    )
    second = decode_token(
        create_token(sub, "access", settings=settings), "access", settings=settings
    )

    assert first.sub == sub
    assert first.expires_at - first.issued_at == timedelta(minutes=settings.jwt_access_ttl_min)
    assert first.jti != second.jti


def _tamper_subject(token: str) -> str:
    header, payload, signature = token.split(".")
    claims = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
    claims["sub"] = new_id()
    forged = base64.urlsafe_b64encode(json.dumps(claims).encode()).rstrip(b"=").decode()
    return f"{header}.{forged}.{signature}"


def _rejected_tokens(settings: Settings) -> dict[str, str]:
    sub = new_id()
    valid = create_token(sub, "access", settings=settings)
    other_secret = make_settings(jwt_secret="another-secret-of-sufficient-length-42")
    return {
        "expired": create_token(sub, "access", timedelta(seconds=-1), settings=settings),
        "wrong_signature": create_token(sub, "access", settings=other_secret),
        "tampered_payload": _tamper_subject(valid),
        "refresh_instead_of_access": create_token(sub, "refresh", settings=settings),
        "missing_claims": jwt.encode({"sub": sub}, settings.jwt_secret, algorithm="HS256"),
        "alg_none": jwt.encode({"sub": sub, "type": "access"}, None, algorithm="none"),
        "garbage": "not.a.jwt",
    }


@pytest.mark.parametrize(
    "case",
    [
        "expired",
        "wrong_signature",
        "tampered_payload",
        "refresh_instead_of_access",
        "missing_claims",
        "alg_none",
        "garbage",
    ],
)
def test_invalid_access_token_is_rejected(settings: Settings, case: str) -> None:
    token = _rejected_tokens(settings)[case]

    with pytest.raises(UnauthorizedError):
        decode_token(token, "access", settings=settings)
