from django import forms
from core.models.people import Person

class PersonForm(forms.ModelForm):
    class Meta:
        model = Person
        fields = [
            "person_type",
            "first_name",
            "last_name",
            "birth_date",
            "bsn",
            "email",
            "phone",
            "street",
            "house_number",
            "postal_code",
            "city",
        ]
        widgets = {
            "person_type": forms.Select(attrs={"class": "form-select"}),
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "birth_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "bsn": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
            "street": forms.TextInput(attrs={"class": "form-control"}),
            "house_number": forms.TextInput(attrs={"class": "form-control"}),
            "postal_code": forms.TextInput(attrs={"class": "form-control"}),
            "city": forms.TextInput(attrs={"class": "form-control"}),
        }