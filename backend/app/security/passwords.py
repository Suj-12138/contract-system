from argon2 import PasswordHasher

_ph = PasswordHasher()


def hash_password(password: str) -> str:
    return _ph.hash(password)


def verify_password(hash_str: str, password: str) -> bool:
    try:
        return _ph.verify(hash_str, password)
    except Exception:
        return False
