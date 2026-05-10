from config.env import get_bool, get_env, get_list, postgres_database_from_env

from .base import *


DEBUG = True
ALLOWED_HOSTS = get_list("DJANGO_ALLOWED_HOSTS", ["localhost", "127.0.0.1", "testserver"])
ONE_CLICK_LOGIN_ENABLED = get_bool("DJANGO_ENABLE_ONE_CLICK_LOGIN", get_bool("DJANGO_ALLOW_SQLITE_BOOTSTRAP", False))
ONE_CLICK_LOGIN_USERNAME = get_env("DJANGO_ONE_CLICK_LOGIN_USERNAME", "owner")
ONE_CLICK_LOGIN_PASSWORD = get_env("DJANGO_ONE_CLICK_LOGIN_PASSWORD", "ChangeMe123!")

if get_bool("DJANGO_ALLOW_SQLITE_BOOTSTRAP", False):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "dev-bootstrap.sqlite3",
        }
    }
else:
    DATABASES = {
        "default": postgres_database_from_env(),
    }
