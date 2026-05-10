from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model, login as auth_login
from django.http import Http404
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST


def csrf_failure(request, reason="", template_name="errors/csrf_failure.html"):
    return render(
        request,
        template_name,
        {
            "reason": reason,
            "request_path": request.path,
        },
        status=403,
    )


@require_POST
def quick_login_view(request):
    if not getattr(settings, "ONE_CLICK_LOGIN_ENABLED", False):
        raise Http404("Quick login is not enabled.")

    User = get_user_model()
    username = getattr(settings, "ONE_CLICK_LOGIN_USERNAME", "owner")
    password = getattr(settings, "ONE_CLICK_LOGIN_PASSWORD", "ChangeMe123!")

    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            "is_staff": True,
            "is_superuser": True,
            "is_active": True,
        },
    )

    if created:
        user.set_password(password)
        user.save(update_fields=["password"])
    elif not user.is_active:
        user.is_active = True
        user.save(update_fields=["is_active"])

    auth_login(request, user, backend="django.contrib.auth.backends.ModelBackend")
    messages.success(request, "已通过本地一键登录进入系统。")

    next_url = request.POST.get("next", "")
    if next_url and url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return redirect(next_url)
    return redirect("dashboard:home")
