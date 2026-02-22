from django.contrib.contenttypes.fields import GenericRelation
from django.conf import settings
from django.db import models
from django.utils import timezone

from .base import TimeStampedModel
from .status import Status
from .types import SignalType, TaskType
from .notes import Note
from .history import HistoryEvent  # zie hieronder

# -------------------------
# Core entities
# -------------------------

class Signal(TimeStampedModel):
    type = models.ForeignKey(SignalType, on_delete=models.PROTECT, related_name="signals")
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="assigned_signals",
        help_text="Leeg = zichtbaar voor alle users (default)."
    )

    active_from = models.DateTimeField(default=timezone.now)
    status = models.ForeignKey(Status, on_delete=models.PROTECT, null=True, blank=True, related_name="signals")
    notes = GenericRelation(Note, related_query_name="signals")
    history = GenericRelation(HistoryEvent, related_query_name="signals")

    body = models.TextField()  # alleen omschrijving, geen aparte title
    is_archived = models.BooleanField(default=False)

    def __str__(self):
        return f"Signal #{self.id}"

class Task(TimeStampedModel):
    type = models.ForeignKey(TaskType, on_delete=models.PROTECT, related_name="tasks")
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="tasks")

    due_at = models.DateTimeField(null=True, blank=True)
    status = models.ForeignKey(Status, on_delete=models.PROTECT, null=True, blank=True, related_name="tasks")
    notes = GenericRelation(Note, related_query_name="tasks")
    history = GenericRelation(HistoryEvent, related_query_name="tasks")

    body = models.TextField(blank=True)
    is_archived = models.BooleanField(default=False)

    def __str__(self):
        return f"Task #{self.id}"