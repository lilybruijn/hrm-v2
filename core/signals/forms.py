from django import forms
from django.contrib.auth import get_user_model
from django.utils import timezone
from core.models import Signal, Note, SignalType, Status, Person

User = get_user_model()

class SignalForm(forms.ModelForm):
    class Meta:
        model = Signal
        fields = ["name", "people", "type", "active_from", "status", "assigned_to", "body"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        if "name" in self.fields:
            self.fields["name"].widget.attrs.update({
                "class": "form-control form-control-sm",
                "placeholder": "Korte titel van de melding"
            })
        
        if "people" in self.fields:
            self.fields["people"].queryset = Person.objects.order_by("last_name", "first_name")
            self.fields["people"].required = False
            self.fields["people"].widget.attrs.update({"class": "form-select form-select-sm js-multiselect"})

        if "status" in self.fields:
            qs = Status.objects.filter(scope="signal", is_active=True).order_by("sort_order", "name")
            if self.instance.pk and self.instance.status_id:
                qs = qs | Status.objects.filter(pk=self.instance.status_id)

            self.fields["status"].queryset = qs.distinct()
            self.fields["status"].required = False
            self.fields["status"].label_from_instance = lambda obj: obj.name

        if "type" in self.fields:
            qs = SignalType.objects.filter(is_active=True).order_by("sort_order", "name")
            if self.instance.pk and self.instance.type_id:
                qs = qs | SignalType.objects.filter(pk=self.instance.type_id)

            self.fields["type"].queryset = qs.distinct()
            self.fields["type"].required = False

        if "assigned_to" in self.fields:
            self.fields["assigned_to"].queryset = User.objects.filter(is_staff=True, is_active=True).order_by("username")
            self.fields["assigned_to"].required = False
            self.fields["assigned_to"].empty_label = "Niet toegewezen"

        for name, field in self.fields.items():
            if name == "people":
                continue
            is_select = field.widget.__class__.__name__.lower().find("select") >= 0
            field.widget.attrs["class"] = "form-select form-select-sm" if is_select else "form-control form-control-sm"

        if "body" in self.fields:
            self.fields["body"].widget.attrs["rows"] = 3

        if "active_from" in self.fields:
            self.fields["active_from"].widget = forms.DateInput(
                attrs={"type": "date", "class": "form-control form-control-sm"},
                format="%Y-%m-%d",
            )

        if not self.instance.pk and not self.initial.get("active_from"):
            self.fields["active_from"].initial = timezone.localdate()

class NoteForm(forms.ModelForm):
    class Meta:
        model = Note
        fields = ["body"]
        widgets = {
            "body": forms.Textarea(attrs={
                "rows": 3,
                "placeholder": "Nieuwe notitie",
                "class": "form-control"
            })
        }