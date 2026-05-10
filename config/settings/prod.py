from config.env import postgres_database_from_env

from .base import *


DEBUG = False
DATABASES = {
    "default": postgres_database_from_env(),
}
