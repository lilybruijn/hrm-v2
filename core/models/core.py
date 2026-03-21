from django.contrib.contenttypes.fields import GenericRelation
from django.conf import settings
from django.db import models
from django.utils import timezone

from .base import TimeStampedModel
from .status import Status
from .types import SignalType, TaskType
from .notes import Note
from .people import Person
from .history import HistoryEvent  # zie hieronder
from .settings import SettingOption
from .people import Person, StudentProfile, EmployeeProfile
from .organizations import Organization
from .contacts import ContactPerson, PersonContact

# -------------------------
# Core entities
# -------------------------
class Signal(TimeStampedModel):
    type = models.ForeignKey(SignalType, on_delete=models.PROTECT, related_name="signals")

    people = models.ManyToManyField(
        Person,
        blank=True,
        related_name="signals",
    )

    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="assigned_signals",
        help_text="Leeg = zichtbaar voor alle users (default)."
    )
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_signal_assignments",
    )
    
    name = models.CharField(max_length=200, blank=True)

    active_from = models.DateField(default=timezone.localdate)
    status = models.ForeignKey(Status, on_delete=models.PROTECT, null=True, blank=True, related_name="signals")
    notes = GenericRelation(Note, related_query_name="signals")
    history = GenericRelation(HistoryEvent, related_query_name="signals")

    body = models.TextField()
    is_archived = models.BooleanField(default=False)

    def __str__(self):
        return f"Signal #{self.id}"


class Task(TimeStampedModel):
    parent_task = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="child_tasks",
    )
        
    type = models.ForeignKey(TaskType, on_delete=models.PROTECT, related_name="tasks")

    people = models.ManyToManyField(
        Person,
        blank=True,
        related_name="tasks",
    )

    signal = models.ForeignKey(
        "core.Signal",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tasks",
    )

    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="tasks")

    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_task_assignments",
    )
    due_at = models.DateField(default=timezone.localdate)
    status = models.ForeignKey(Status, on_delete=models.PROTECT, null=True, blank=True, related_name="tasks")
    notes = GenericRelation(Note, related_query_name="tasks")
    history = GenericRelation(HistoryEvent, related_query_name="tasks")

    body = models.TextField(blank=True)
    is_archived = models.BooleanField(default=False)

    def __str__(self):
        return f"Task #{self.id}"