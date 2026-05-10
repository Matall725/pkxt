from django.urls import path

from .views import (
    payment_entry_create_view,
    receivable_create_view,
    receivable_list_view,
    receivable_update_view,
)


app_name = "payments"

urlpatterns = [
    path("", receivable_list_view, name="list"),
    path("new/", receivable_create_view, name="create"),
    path("<int:pk>/edit/", receivable_update_view, name="update"),
    path("<int:receivable_id>/entries/new/", payment_entry_create_view, name="entry-create"),
]
