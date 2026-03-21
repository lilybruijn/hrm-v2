from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST

User = get_user_model()


@login_required
@require_POST
def impersonate_start(request, user_id):
    if not request.user.is_staff:
        return HttpResponseForbidden("Forbidden")

    target_user = get_object_or_404(User, pk=user_id, is_active=True)

    if target_user.id == request.user.id:
        messages.info(request, "Je bent al ingelogd als deze gebruiker.")
        return redirect("dashboard")

    request.session["impersonator_id"] = request.user.id
    request.session["impersonate_user_id"] = target_user.id

    messages.success(request, f"Je bekijkt het portaal nu als {target_user.username}.")
    return redirect("dashboard")


@login_required
@require_POST
def impersonate_stop(request):
    impersonator_id = request.session.get("impersonator_id")

    if not impersonator_id:
        messages.info(request, "Er is geen actieve bekijk-als sessie.")
        return redirect("dashboard")

    if request.real_user.is_authenticated and request.real_user.id == impersonator_id:
        request.session.pop("impersonate_user_id", None)
        request.session.pop("impersonator_id", None)
        messages.success(request, "Je bent teruggeschakeld naar je eigen admin-account.")

    return redirect("dashboard")