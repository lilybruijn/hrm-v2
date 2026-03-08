from django import forms
from django.contrib.auth import get_user_model
from django.utils import timezone

from core.models import Task, Status, TaskType, Person, Signal

User = get_user_model()

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ["people", "signal", "type", "assigned_to", "due_at", "status", "body"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if "people" in self.fields:
            self.fields["people"].queryset = Person.objects.order_by("last_name", "first_name")
            self.fields["people"].required = False
            self.fields["people"].widget.attrs.update({"class": "form-select form-select-sm js-multiselect"})

        if "signal" in self.fields:
            self.fields["signal"].queryset = Signal.objects.select_related("type").order_by("-created_at")
            self.fields["signal"].required = False
            self.fields["signal"].label_from_instance = lambda obj: f"Melding #{obj.id}: {obj.name}"
            self.fields["signal"].widget.attrs.update({"class": "form-select form-select-sm js-select"})

        if "status" in self.fields:
            qs = Status.objects.filter(scope="task", is_active=True).order_by("sort_order", "name")
            if self.instance.pk and self.instance.status_id:
                qs = qs | Status.objects.filter(pk=self.instance.status_id)

            self.fields["status"].queryset = qs.distinct()
            self.fields["status"].required = False
            self.fields["status"].label_from_instance = lambda obj: obj.name

        if "type" in self.fields:
            self.fields["type"].queryset = TaskType.objects.filter(is_active=True).order_by("sort_order", "name")

        if "assigned_to" in self.fields:
            self.fields["assigned_to"].queryset = User.objects.filter(is_staff=True, is_active=True).order_by("username")
            self.fields["assigned_to"].required = True

        for name, field in self.fields.items():
            existing_class = field.widget.attrs.get("class", "")
            if name == "body":
                continue

            is_select = field.widget.__class__.__name__.lower().find("select") >= 0
            base_class = "form-select form-select-sm" if is_select else "form-control form-control-sm"

            if base_class not in existing_class:
                field.widget.attrs["class"] = f"{existing_class} {base_class}".strip()

            field.widget.attrs["autocomplete"] = "off"

        if "body" in self.fields:
            self.fields["body"].widget = forms.Textarea(
                attrs={"rows": 3, "class": "form-control form-control-sm"}
            )

        if not self.instance.pk and not self.initial.get("due_at"):
            self.fields["due_at"].initial = timezone.localdate()

class TaskCreateForm(TaskForm):
    class Meta(TaskForm.Meta):
        widgets = {
            "people": forms.SelectMultiple(
                attrs={"class": "form-select form-select-sm js-multiselect", "size": 6}
            ),
            "due_at": forms.DateInput(
                attrs={"type": "date", "class": "form-control form-control-sm"},
                format="%Y-%m-%d",
            ),
        }