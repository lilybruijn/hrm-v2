from __future__ import annotations

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.db import transaction

from core.models import HistoryEvent, Notification, Signal

User = get_user_model()


def log_history(obj, actor, action: str, changes: dict | None = None):
    HistoryEvent.objects.create(
        content_type=ContentType.objects.get_for_model(obj.__class__),
        object_id=obj.id,
        actor=actor if getattr(actor, "is_authenticated", False) else None,
        action=action,
        changes=changes or {},
    )


@transaction.atomic
def create_signal_notifications(signal: Signal, created_by):
    """
    Regels:
    - assigned_to gezet -> notificatie alleen voor die user
    - assigned_to leeg -> notificatie voor alle staff users
    """
    title = "Nieuwe melding"
    body = (signal.body or "")[:4000]
    url = f"/signals/{signal.id}/"

    if signal.assigned_to_id:
        Notification.objects.create(
            user=signal.assigned_to,
            content_object=signal,
            title=title,
            body=body,
            url=url,
        )
        return

    staff_users = User.objects.filter(is_staff=True, is_active=True).exclude(id=getattr(created_by, "id", None))
    Notification.objects.bulk_create([
        Notification(
            user=u,
            content_object=signal,
            title=title,
            body=body,
            url=url,
        )
        for u in staff_users
    ])