import os

from config.bootstrap import configure_local_packages
from django.core.asgi import get_asgi_application


configure_local_packages()
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

application = get_asgi_application()
