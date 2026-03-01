from django import forms
from django.contrib.auth import get_user_model
from django.utils import timezone
from core.models import Signal, Note, SignalType, Status

User = get_user_model()

class SignalForm(forms.ModelForm):
    class Meta:
        model = Signal
        fields = ["type", "active_from", "status", "assigned_to", "body"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Status queryset (met huidige value erbij)
        if "status" in self.fields:
            qs = Status.objects.filter(scope="signal", is_active=True).order_by("sort_order", "name")

            # ✅ zorg dat huidige status ook beschikbaar is (ook als inactive)
            if self.instance.pk and self.instance.status_id:
                qs = qs | Status.objects.filter(pk=self.instance.status_id)

            self.fields["status"].queryset = qs.distinct()
            self.fields["status"].required = False

            # ✅ dropdown label alleen de naam (niet "signal: ...")
            self.fields["status"].label_from_instance = lambda obj: obj.name

        # Type queryset (met huidige value erbij)
        if "type" in self.fields:
            qs = SignalType.objects.filter(is_active=True).order_by("sort_order", "name")
            # (als SignalType toch scope heeft: filter(scope="signal", is_active=True))

            if self.instance.pk and self.instance.type_id:
                qs = qs | SignalType.objects.filter(pk=self.instance.type_id)

            self.fields["type"].queryset = qs.distinct()
            self.fields["type"].required = False

        self.fields["assigned_to"].queryset = User.objects.filter(is_staff=True).order_by("username")
        self.fields["assigned_to"].required = False

        for name, field in self.fields.items():
            is_select = field.widget.__class__.__name__.lower().find("select") >= 0
            field.widget.attrs["class"] = "form-select form-select-sm" if is_select else "form-control form-control-sm"

        self.fields["body"].widget.attrs["rows"] = 3

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