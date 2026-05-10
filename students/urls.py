from django.urls import path

from .views import student_create_view, student_list_view, student_update_view


app_name = "students"

urlpatterns = [
    path("", student_list_view, name="list"),
    path("new/", student_create_view, name="create"),
    path("<int:pk>/edit/", student_update_view, name="update"),
]
