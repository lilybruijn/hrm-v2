from django import forms
from core.models import WageValuePeriod, Organization, Person, SettingOption


class WageValuePeriodForm(forms.ModelForm):
    class Meta:
        model = WageValuePeriod
        fields = [
            "person",
            "organization",
            "status",
            "decision_status",
            "start_date",
            "end_date",
            "percentage",
            "meeting_date",
            "meeting_location",
            "meeting_attendees",
            "notes",
        ]
        widgets = {
            "person": forms.Select(attrs={"class": "form-select js-select"}),
            "organization": forms.Select(attrs={"class": "form-select js-select"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "decision_status": forms.Select(attrs={"class": "form-select"}),
            "start_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "end_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "percentage": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "meeting_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "meeting_location": forms.TextInput(attrs={"class": "form-control"}),
            "meeting_attendees": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        person = kwargs.pop("person", None)
        super().__init__(*args, **kwargs)

        self.fields["person"].queryset = Person.objects.filter(
            person_type="employee",
            is_archived=False,
        ).order_by("last_name", "first_name")

        self.fields["organization"].queryset = Organization.objects.filter(
            is_archived=False,
        ).order_by("name")

        self.fields["status"].queryset = SettingOption.objects.filter(
            category="wage_value_status",
            is_active=True,
        ).order_by("sort_order", "label")

        self.fields["decision_status"].queryset = SettingOption.objects.filter(
            category="wage_value_decision_status",
            is_active=True,
        ).order_by("sort_order", "label")

        if person:
            self.fields["person"].initial = person