from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from core.models import Notification


@login_required
def notification_list(request):
    notifications = Notification.objects.filter(user=request.user)

    return render(request, "core/notifications/list.html", {
        "notifications": notifications,
        "active_nav": "notifications",
    })


@login_required
@require_POST
def notification_mark_read(request, pk: int):
    notification = get_object_or_404(
        Notification,
        pk=pk,
        user=request.user,
    )

    if not notification.is_read:
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save(update_fields=["is_read", "read_at"])

    if notification.url:
        return redirect(notification.url)

    return redirect("notifications:list")


@login_required
@require_POST
def notification_mark_all_read(request):
    Notification.objects.filter(
        user=request.user,
        is_read=False,
    ).update(
        is_read=True,
        read_at=timezone.now(),
    )

    return redirect("notifications:list")