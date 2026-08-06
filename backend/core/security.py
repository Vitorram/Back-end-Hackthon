import hashlib
import os
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from dotenv import load_dotenv
from jose import JWTError, jwt

load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

if not SECRET_KEY:
    raise RuntimeError("JWT_SECRET_KEY nao configurado no .env")


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _create_token(data: dict, token_type: str, expires_delta: timedelta) -> str:
    payload = data.copy()
    now = _now_utc()
    expire = now + expires_delta

    payload.update({
        "exp": expire,
        "iat": now,
        "nbf": now,
        "typ": token_type,
        "jti": str(uuid4()),
    })

    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_access_token(data: dict) -> str:
    return _create_token(
        data=data,
        token_type="access",
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )


def create_refresh_token(data: dict) -> str:
    return _create_token(
        data=data,
        token_type="refresh",
        expires_delta=timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
    )


def decode_token(token: str, expected_type: str) -> dict | None:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None

    if payload.get("typ") != expected_type:
        return None

    return payload


def decode_access_token(token: str) -> dict | None:
    return decode_token(token, expected_type="access")


def decode_refresh_token(token: str) -> dict | None:
    return decode_token(token, expected_type="refresh")


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def get_token_expiration(token: str) -> datetime | None:
    payload = jwt.get_unverified_claims(token)
    exp = payload.get("exp")
    if exp is None:
        return None

    return datetime.fromtimestamp(exp, timezone.utc)
