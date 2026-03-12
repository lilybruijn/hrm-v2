# core/models/organizations.py
from django.db import models


class Organization(models.Model):
    name = models.CharField(max_length=255)
    organization_type = models.ForeignKey(
        "SettingOption",
        on_delete=models.PROTECT,
        related_name="organizations",
        limit_choices_to={"category": "organization_type"},
    )

    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)

    street = models.CharField(max_length=255, blank=True)
    house_number = models.CharField(max_length=20, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    city = models.CharField(max_length=100, blank=True)

    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name