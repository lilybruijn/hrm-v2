from django.db import models


class Status(models.Model):
    SCOPE_CHOICES = (
        ("signal", "Signal"),
        ("task", "Task"),
    )

    key = models.SlugField(max_length=50)
    name = models.CharField(max_length=80)

    scope = models.CharField(max_length=10, choices=SCOPE_CHOICES)  # signal/task
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = (("scope", "key"),)
        ordering = ("scope", "sort_order", "name")

    def __str__(self):
        return f"{self.scope}: {self.name}"