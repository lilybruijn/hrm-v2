from django import forms

from core.models import ContactPerson, Organization


class ContactPersonForm(forms.ModelForm):
    class Meta:
        model = ContactPerson
        fields = [
            "first_name",
            "last_name",
            "email",
            "phone",
            "job_title",
            "organization",
            "notes",
            "is_active",
        ]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control form-control-sm"}),
            "last_name": forms.TextInput(attrs={"class": "form-control form-control-sm"}),
            "email": forms.EmailInput(attrs={"class": "form-control form-control-sm"}),
            "phone": forms.TextInput(attrs={"class": "form-control form-control-sm"}),
            "job_title": forms.TextInput(attrs={"class": "form-control form-control-sm"}),
            "organization": forms.Select(attrs={"class": "form-select form-select-sm"}),
            "notes": forms.Textarea(attrs={"class": "form-control form-control-sm", "rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        person_id = kwargs.pop("person_id", None)
        super().__init__(*args, **kwargs)

        self.fields["organization"].required = False
        self.fields["organization"].queryset = Organization.objects.order_by("name")