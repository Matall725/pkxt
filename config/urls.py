from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

from config import views as config_views


urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/login/", auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("accounts/quick-login/", config_views.quick_login_view, name="quick-login"),
    path("accounts/logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("students/", include("students.urls")),
    path("", include("dashboard.urls")),
    path("schedules/", include("schedules.urls")),
    path("sessions/", include("sessions.urls")),
    path("notes/", include("notes.urls")),
    path("payments/", include("payments.urls")),
    path("reminders/", include("reminders.urls")),
    path("ai/", include("ai_gateway.urls")),
]
