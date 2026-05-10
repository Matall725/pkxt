from django.urls import path

from .views import note_create_view, note_update_view


app_name = "notes"

urlpatterns = [
    path("schedule/<int:schedule_id>/new/", note_create_view, name="create"),
    path("<int:pk>/edit/", note_update_view, name="update"),
]
