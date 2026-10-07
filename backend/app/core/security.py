from dataclasses import dataclass

import jwt

from app.core.errors import UnauthorizedError
from app.utils.time import now_ms

ALGORITHM = "HS256"


@dataclass(frozen=True)
class TokenClaims:
    user_id: str
    session_id: str


def encode_token(*, user_id: str, session_id: str, expires_at_ms: int, secret_key: str) -> str:
    payload = {
        "sub": user_id,
        "sid": session_id,
        "iat": now_ms() // 1000,
        "exp": expires_at_ms // 1000,
    }
    return jwt.encode(payload, secret_key, algorithm=ALGORITHM)


def decode_token(token: str, secret_key: str) -> TokenClaims:
    try:
        payload = jwt.decode(
            token,
            secret_key,
            algorithms=[ALGORITHM],
            options={"require": ["exp", "sub", "sid"]},
        )
    except jwt.ExpiredSignatureError as exc:
        raise UnauthorizedError("Session expired", code="token_expired") from exc
    except jwt.PyJWTError as exc:
        raise UnauthorizedError("Invalid token", code="invalid_token") from exc
    return TokenClaims(user_id=payload["sub"], session_id=payload["sid"])
