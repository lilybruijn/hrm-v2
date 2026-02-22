from django.conf import settings
from django.db import models
from django.utils import timezone

from .status import Status
from .types import SignalType, TaskType

class Signal(models.Model):
    signal_type = models.ForeignKey(SignalType, on_delete=models.PROTECT, related_name="signals")
    status = models.ForeignKey(Status, on_delete=models.PROTECT, related_name="signals")

    body = models.TextField()
    active_from = models.DateTimeField(default=timezone.now)

    # NULL = "voor iedereen" (alle staff users)
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="assigned_signals",
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="created_signals",
    )

    notify = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-active_from", "-created_at"]

    def __str__(self):
        return f"Signal #{self.id}"


class Task(models.Model):
    task_type = models.ForeignKey(TaskType, on_delete=models.PROTECT, related_name="tasks")
    status = models.ForeignKey(Status, on_delete=models.PROTECT, related_name="tasks")

    title = models.CharField(max_length=160)
    description = models.TextField(blank=True)

    due_at = models.DateTimeField(null=True, blank=True)

    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="assigned_tasks",
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="created_tasks",
    )

    notify = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-due_at", "-created_at"]

    def __str__(self):
        return self.title