import os

from config.bootstrap import configure_local_packages
from django.core.wsgi import get_wsgi_application


configure_local_packages()
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

application = get_wsgi_application()
