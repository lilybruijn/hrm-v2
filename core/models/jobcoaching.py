from django.db import models


class JobCoachingPeriod(models.Model):
    person = models.ForeignKey(
        "Person",
        on_delete=models.CASCADE,
        related_name="jobcoaching_periods",
    )
    organization = models.ForeignKey(
        "Organization",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="jobcoaching_periods",
    )
    status = models.ForeignKey(
        "SettingOption",
        on_delete=models.PROTECT,
        related_name="jobcoaching_periods",
        limit_choices_to={"category": "jobcoaching_status"},
    )
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    is_archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-start_date", "-id"]

    def __str__(self):
        return f"Jobcoaching - {self.person.full_name} ({self.start_date})"