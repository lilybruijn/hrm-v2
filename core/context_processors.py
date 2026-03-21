from core.models import Notification


def impersonation_context(request):
    return {
        "is_impersonating": getattr(request, "is_impersonating", False),
        "real_user": getattr(request, "real_user", None),
    }



def notification_context(request):
    if request.user.is_authenticated:
        unread_notifications_count = Notification.objects.filter(
            user=request.user,
            is_read=False,
        ).count()

        recent_notifications = Notification.objects.filter(
            user=request.user,
        ).order_by("-created_at")[:5]
    else:
        unread_notifications_count = 0
        recent_notifications = []

    return {
        "unread_notifications_count": unread_notifications_count,
        "recent_notifications": recent_notifications,
    }