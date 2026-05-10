import os
from typing import Iterable

from django.core.exceptions import ImproperlyConfigured


UNSET = object()


def get_env(name: str, default=UNSET, cast=str):
    value = os.getenv(name)
    if value in (None, ""):
        if default is UNSET:
            raise ImproperlyConfigured(f"Missing required environment variable: {name}")
        return default
    try:
        return cast(value)
    except (TypeError, ValueError) as exc:
        raise ImproperlyConfigured(f"Invalid value for environment variable {name}") from exc


def get_bool(name: str, default=UNSET):
    def cast_bool(raw: str) -> bool:
        normalized = raw.strip().lower()
        if normalized in {"1", "true", "yes", "on"}:
            return True
        if normalized in {"0", "false", "no", "off"}:
            return False
        raise ValueError(name)

    return get_env(name, default=default, cast=cast_bool)


def get_int(name: str, default=UNSET) -> int:
    return get_env(name, default=default, cast=int)


def get_list(name: str, default=UNSET, separator: str = ",") -> list[str]:
    def cast_list(raw: str) -> list[str]:
        return [item.strip() for item in raw.split(separator) if item.strip()]

    if isinstance(default, Iterable) and not isinstance(default, (str, bytes)):
        default = list(default)
    return get_env(name, default=default, cast=cast_list)


def postgres_database_from_env() -> dict:
    return {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": get_env("DB_NAME"),
        "USER": get_env("DB_USER"),
        "PASSWORD": get_env("DB_PASSWORD"),
        "HOST": get_env("DB_HOST"),
        "PORT": get_env("DB_PORT"),
        "CONN_MAX_AGE": get_int("DB_CONN_MAX_AGE", 60),
    }
