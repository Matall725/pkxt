from django.apps import AppConfig
from django.contrib import admin


class DashboardConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "dashboard"
    verbose_name = "工作台"

    def ready(self):
        admin.site.site_header = "家教/咨询排课与收款系统"
        admin.site.site_title = "运营后台"
        admin.site.index_title = "单账号工作台"
