from pathlib import Path

from config.env import get_bool, get_env, get_int, get_list


BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = get_env("DJANGO_SECRET_KEY")
DEBUG = False

ALLOWED_HOSTS = get_list("DJANGO_ALLOWED_HOSTS", ["localhost", "127.0.0.1"])
CSRF_TRUSTED_ORIGINS = get_list("DJANGO_CSRF_TRUSTED_ORIGINS", [])

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "students.apps.StudentsConfig",
    "schedules.apps.SchedulesConfig",
    "sessions.apps.SessionsConfig",
    "payments.apps.PaymentsConfig",
    "notes.apps.NotesConfig",
    "reminders.apps.RemindersConfig",
    "dashboard.apps.DashboardConfig",
    "ai_gateway.apps.AiGatewayConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "config.context_processors.shell_context",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "zh-hans"
TIME_ZONE = "Asia/Shanghai"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "dashboard:home"
LOGOUT_REDIRECT_URL = "login"
CSRF_FAILURE_VIEW = "config.views.csrf_failure"
ONE_CLICK_LOGIN_ENABLED = get_bool("DJANGO_ENABLE_ONE_CLICK_LOGIN", False)
ONE_CLICK_LOGIN_USERNAME = get_env("DJANGO_ONE_CLICK_LOGIN_USERNAME", "owner")
ONE_CLICK_LOGIN_PASSWORD = get_env("DJANGO_ONE_CLICK_LOGIN_PASSWORD", "ChangeMe123!")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

ANTHROPIC_API_KEY = get_env("ANTHROPIC_API_KEY", "dummy-key-for-tests-and-dev")

ADMIN_SITE_HEADER = "家教/咨询排课与收款系统"
ADMIN_SITE_TITLE = "运营后台"
ADMIN_INDEX_TITLE = "单账号工作台"

EXPORT_PAGE_SIZE = get_int("EXPORT_PAGE_SIZE", 1000)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "[%(asctime)s] %(levelname)s %(name)s: %(message)s",
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}

if get_bool("DJANGO_ENABLE_SENTRY", False):
    import sentry_sdk

    sentry_sdk.init(
        dsn=get_env("SENTRY_DSN"),
        traces_sample_rate=0.0,
        send_default_pii=True,
    )
