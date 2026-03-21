from core.models import Notification


def create_notification(*, user, title, message="", type="info", url=""):
    return Notification.objects.create(
        user=user,
        title=title,
        message=message,
        type=type,
        url=url,
    )