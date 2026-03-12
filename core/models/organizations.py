from django.db import models


class Organization(models.Model):
    name = models.CharField(max_length=255)
    organization_type = models.ForeignKey(
        "SettingOption",
        on_delete=models.PROTECT,
        related_name="organizations",
        limit_choices_to={"category": "organization_type"},
    )
    is_archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name