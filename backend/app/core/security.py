import hashlib
import hmac
import secrets

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

# Argon2id нь argon2-cffi-ийн анхдагч (time=3, memory=64MiB, parallelism=4).
_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def needs_rehash(password_hash: str) -> bool:
    try:
        return _hasher.check_needs_rehash(password_hash)
    except InvalidHashError:
        return False


def generate_token() -> str:
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def generate_csrf_token() -> str:
    return secrets.token_urlsafe(32)


def csrf_matches(expected: str, provided: str | None) -> bool:
    if not provided:
        return False
    return hmac.compare_digest(expected, provided)


def password_policy_errors(password: str) -> list[str]:
    errors: list[str] = []
    if len(password) < 10:
        errors.append("Нууц үг дор хаяж 10 тэмдэгт байх ёстой.")
    if len(password) > 128:
        errors.append("Нууц үг 128 тэмдэгтээс хэтрэхгүй байх ёстой.")
    if not any(ch.isalpha() for ch in password):
        errors.append("Нууц үг дор хаяж нэг үсэг агуулсан байх ёстой.")
    if not any(ch.isdigit() for ch in password):
        errors.append("Нууц үг дор хаяж нэг тоо агуулсан байх ёстой.")
    return errors
