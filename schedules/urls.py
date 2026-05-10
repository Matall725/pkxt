from django.urls import path

from .views import calendar_events, calendar_view, schedule_create_view, schedule_update_view


app_name = "schedules"

urlpatterns = [
    path("", calendar_view, name="calendar"),
    path("events/", calendar_events, name="events"),
    path("new/", schedule_create_view, name="create"),
    path("<int:pk>/edit/", schedule_update_view, name="update"),
]
