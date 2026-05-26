from django.urls import path
from . import views

app_name = "ai_gateway"

urlpatterns = [
    path("copilot/stream/", views.stream_copilot_response, name="copilot_stream"),
    path("copilot/approve-proposal/", views.approve_proposal, name="approve_proposal"),
    path("copilot/reject-proposal/", views.reject_proposal, name="reject_proposal"),
    path("feedback/generate/", views.generate_feedback, name="generate_feedback"),
    path("reminder/draft/", views.draft_payment_reminder, name="draft_payment_reminder"),
    path("student-portrait/", views.student_portrait, name="student_portrait"),
]
