from django.conf import settings

from reminders.models import ReminderTask


def shell_context(request):
    context = {
        "one_click_login_enabled": getattr(settings, "ONE_CLICK_LOGIN_ENABLED", False),
    }
    if not request.user.is_authenticated:
        return context

    full_name = request.user.get_full_name().strip()
    user_label = full_name or request.user.username
    pending_reminders = ReminderTask.objects.filter(status=ReminderTask.Status.PENDING).count()

    context.update(
        {
            "shell_pending_reminders": pending_reminders,
            "shell_user_label": user_label,
        }
    )
    return context
