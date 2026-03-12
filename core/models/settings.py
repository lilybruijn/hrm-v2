# core/models/settings.py
from django.db import models

class SettingOption(models.Model):
    category = models.CharField(max_length=100)
    code = models.CharField(max_length=100)
    label = models.CharField(max_length=255)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["category", "sort_order", "label"]
        unique_together = ("category", "code")

    def __str__(self):
        return f"{self.category} - {self.label}"