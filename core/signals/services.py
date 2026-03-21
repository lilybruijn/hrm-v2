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


def create_signal_notifications(signal, actor, reassigned=False):
    if not signal.assigned_to:
        return None

    if reassigned:
        title = "Melding aan jou toegewezen"
        message = f"{actor.username} heeft de melding '{signal.name}' aan je toegewezen."
    else:
        title = "Nieuwe melding toegewezen"
        message = f"{actor.username} heeft een nieuwe melding aan je toegewezen: '{signal.name}'."

    return Notification.objects.create(
        user=signal.assigned_to,
        title=title,
        message=message,
        type="warning",
        url=f"/signals/{signal.pk}/",
    )