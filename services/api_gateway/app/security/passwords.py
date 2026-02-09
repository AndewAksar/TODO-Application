from __future__ import annotations

from typing import cast

from passlib.context import CryptContext

_pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)


def hash_password(plain_password: str) -> str:
    """
    Захешировать пароль.

    Принимает:
    - plain_password: пароль в открытом виде (строка).

    Возвращает:
    - строку bcrypt-хеша, пригодную для хранения в БД.

    Важно:
    - bcrypt сам генерирует соль.
    - соль и cost-factor зашиваются внутрь строки хеша.
    - ничего дополнительно хранить не нужно.
    """
    if not isinstance(plain_password, str):
        raise TypeError("error: plain_password must be a string")

    if not plain_password:
        raise ValueError("error: plain_password must not be empty")

    return cast(str, _pwd_context.hash(plain_password))


def verify_password(plain_password: str, password_hash: str) -> bool:
    """
    Проверить пароль.

    Возвращает:
    - True — если пароль совпадает с хешем
    - False — если не совпадает или хеш некорректен

    Почему bool, а не исключение:
    - неверный пароль — штатная ситуация (login)
    - исключения оставляем для действительно аварийных сценариев
    """
    if not isinstance(plain_password, str):
        raise TypeError("error: plain_password must be a string")

    if not isinstance(password_hash, str):
        raise TypeError("error: password_hash must be a string")

    try:
        return cast(bool, _pwd_context.verify(plain_password, password_hash))
    except Exception:
        # Битый или неподдерживаемый хеш считаем несовпадением.
        return False
