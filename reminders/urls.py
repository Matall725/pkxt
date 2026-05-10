from django.urls import path

from .views import reminder_center_view, reminder_done_view, reminder_scan_view


app_name = "reminders"

urlpatterns = [
    path("", reminder_center_view, name="center"),
    path("scan/", reminder_scan_view, name="scan"),
    path("<int:pk>/done/", reminder_done_view, name="done"),
]
