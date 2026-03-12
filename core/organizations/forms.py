from django import forms
from core.models import Organization, SettingOption


class OrganizationForm(forms.ModelForm):
    class Meta:
        model = Organization
        fields = ["name", "organization_type"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "organization_type": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["organization_type"].queryset = SettingOption.objects.filter(
            category="organization_type",
            is_active=True,
        ).order_by("sort_order", "label")