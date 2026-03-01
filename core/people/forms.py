from django import forms
from core.models.people import Person

class PersonForm(forms.ModelForm):
    class Meta:
        model = Person
        fields = ["person_type", "first_name", "last_name", "email", "phone", "notes"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for name, field in self.fields.items():
            is_select = field.widget.__class__.__name__.lower().find("select") >= 0
            field.widget.attrs.update({
                "class": "form-select form-select-sm" if is_select else "form-control form-control-sm",
                "autocomplete": "off",
            })

        if "notes" in self.fields:
            self.fields["notes"].widget = forms.Textarea(
                attrs={"rows": 3, "class": "form-control form-control-sm"}
            )