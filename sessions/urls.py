from django.urls import path

from .views import complete_schedule_view


app_name = "sessions"

urlpatterns = [
    path("schedule/<int:schedule_id>/complete/", complete_schedule_view, name="complete"),
]
