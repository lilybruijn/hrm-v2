from django import forms

from core.models.types import SignalType, TaskType
from core.models.status import Status


# =========================
# BASE STYLING MIXIN
# =========================

class BootstrapFormMixin:
    def _apply_bootstrap(self):
        for field in self.fields.values():
            widget = field.widget

            if isinstance(widget, forms.CheckboxInput):
                widget.attrs["class"] = "form-check-input"
            else:
                existing = widget.attrs.get("class", "")
                widget.attrs["class"] = f"{existing} form-control".strip()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap()


# =========================
# SIGNAL TYPE
# =========================

class SignalTypeForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = SignalType
        fields = ["name", "sort_order", "is_active"]
        labels = {
            "name": "Naam",
            "sort_order": "Volgorde",
            "is_active": "Actief",
        }


# =========================
# TASK TYPE
# =========================

class TaskTypeForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = TaskType
        fields = ["name", "sort_order", "is_active"]
        labels = {
            "name": "Naam",
            "sort_order": "Volgorde",
            "is_active": "Actief",
        }


# =========================
# STATUS (SIGNAL + TASK)
# =========================

class StatusForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Status
        fields = ["name", "sort_order", "is_active"]
        labels = {
            "name": "Naam",
            "sort_order": "Volgorde",
            "is_active": "Actief",
        }