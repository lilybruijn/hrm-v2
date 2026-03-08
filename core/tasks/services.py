from __future__ import annotations

from django.contrib.auth import get_user_model
from django.db import transaction

from core.models import Notification, Task

User = get_user_model()


@transaction.atomic
def create_task_notifications(task: Task, created_by):
    if not task.assigned_to_id:
        return

    Notification.objects.create(
        user=task.assigned_to,
        content_object=task,
        title="Nieuwe taak",
        body=(task.body or "")[:4000],
        url=f"/tasks/{task.id}/",
    )