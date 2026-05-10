from django.urls import path

from .views import (
    export_finance_report,
    export_hours_report,
    export_receivables_csv,
    export_students_csv,
    home,
    report_center,
)


app_name = "dashboard"

urlpatterns = [
    path("", home, name="home"),
    path("reports/", report_center, name="reports"),
    path("reports/students.csv", export_students_csv, name="export-students"),
    path("reports/receivables.csv", export_receivables_csv, name="export-receivables"),
    path("reports/hours.xlsx", export_hours_report, name="export-hours"),
    path("reports/finance.xlsx", export_finance_report, name="export-finance"),
]
