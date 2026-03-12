from django.db import models


class WageValuePeriod(models.Model):
    person = models.ForeignKey(
        "Person",
        on_delete=models.CASCADE,
        related_name="wage_value_periods",
    )
    organization = models.ForeignKey(
        "Organization",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="wage_value_periods",
    )
    status = models.ForeignKey(
        "SettingOption",
        on_delete=models.PROTECT,
        related_name="wage_value_periods",
        limit_choices_to={"category": "wage_value_status"},
    )
    decision_status = models.ForeignKey(
        "SettingOption",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="wage_value_decisions",
        limit_choices_to={"category": "wage_value_decision_status"},
    )
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    meeting_date = models.DateField(null=True, blank=True)
    meeting_location = models.CharField(max_length=255, blank=True)
    meeting_attendees = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    is_archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-start_date", "-id"]

    def __str__(self):
        return f"Loonwaarde - {self.person.full_name} ({self.start_date})"