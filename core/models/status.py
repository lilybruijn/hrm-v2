from django.db import models
from .base import TimeStampedModel

# -------------------------
# Status system
# -------------------------

class StatusSet(TimeStampedModel):
    key = models.SlugField(unique=True)   # "signals", "tasks"
    name = models.CharField(max_length=120)
    enabled = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Status(TimeStampedModel):
    status_set = models.ForeignKey(StatusSet, on_delete=models.CASCADE, related_name="statuses")
    key = models.SlugField()              # "open", "done", "in_progress"
    label = models.CharField(max_length=120)
    sort_order = models.PositiveIntegerField(default=0)

    is_done = models.BooleanField(default=False)
    is_default = models.BooleanField(default=False)

    class Meta:
        unique_together = (("status_set", "key"),)
        ordering = ("status_set", "sort_order", "label")

    def __str__(self):
        return f"{self.status_set.key}: {self.label}"


class StatusUsage(TimeStampedModel):
    MODULE_CHOICES = [
        ("signals", "Signals"),
        ("tasks", "Tasks"),
        ("messages", "Messages"),
    ]
    module_key = models.CharField(max_length=32, choices=MODULE_CHOICES, unique=True)
    enabled = models.BooleanField(default=True)
    status_set = models.ForeignKey(StatusSet, on_delete=models.PROTECT, null=True, blank=True)

    def __str__(self):
        return f"{self.module_key} -> {self.status_set_id or '-'} ({'on' if self.enabled else 'off'})"
