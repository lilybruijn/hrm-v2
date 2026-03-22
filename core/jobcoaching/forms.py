from django import forms
from core.models import JobCoachingPeriod, Organization, Person, SettingOption


class JobCoachingPeriodForm(forms.ModelForm):
    class Meta:
        model = JobCoachingPeriod
        fields = [
            "person",
            "organization",
            "status",
            "start_date",
            "end_date",
            "notes",
        ]
        widgets = {
            "person": forms.Select(attrs={"class": "form-select js-select"}),
            "organization": forms.Select(attrs={"class": "form-select js-select"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "start_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}, format="%Y-%m-%d"),
            "end_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}, format="%Y-%m-%d"),
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
            category="jobcoaching_status",
            is_active=True,
        ).order_by("sort_order", "label")

        if person:
            self.fields["person"].initial = person