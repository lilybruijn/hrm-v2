from django import forms
from django.contrib.auth import get_user_model
from django.utils import timezone

from core.models import Task, Status, TaskType

User = get_user_model()


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ["type", "assigned_to", "due_at", "status", "body"]
        widgets = {
            "due_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Bootstrap compact
        for name, field in self.fields.items():
            is_select = field.widget.__class__.__name__.lower().find("select") >= 0
            field.widget.attrs.update({
                "class": "form-select form-select-sm" if is_select else "form-control form-control-sm",
                "autocomplete": "off",
            })

        if "body" in self.fields:
            self.fields["body"].widget = forms.Textarea(
                attrs={"rows": 3, "class": "form-control form-control-sm"}
            )

        # Default due_at bij create (optioneel): nu + 1 dag 09:00
        if "due_at" in self.fields and not self.instance.pk and not self.initial.get("due_at"):
            now = timezone.localtime()
            default = now.replace(hour=9, minute=0, second=0, microsecond=0) + timezone.timedelta(days=1)
            self.fields["due_at"].initial = default

        # Alleen statuses voor tasks
        if "status" in self.fields:
            qs = Status.objects.filter(scope="task", is_active=True).order_by("sort_order", "name")
            if self.instance.pk and self.instance.status_id:
                qs = qs | Status.objects.filter(pk=self.instance.status_id)
            self.fields["status"].queryset = qs.distinct()
            self.fields["status"].required = False  # status mag null

        # Alleen types voor tasks (als TaskType ook scope heeft, filter scope="task")
        if "type" in self.fields:
            self.fields["type"].queryset = TaskType.objects.filter(is_active=True).order_by("sort_order", "name")

        # Assigned_to is verplicht in jouw model -> required True (default)
        if "assigned_to" in self.fields:
            self.fields["assigned_to"].queryset = User.objects.filter(is_staff=True, is_active=True).order_by("username")
            self.fields["assigned_to"].required = True