from django import forms
from core.models.people import StudentProfile


class StudentProfileForm(forms.ModelForm):
    class Meta:
        model = StudentProfile
        fields = [
            "is_active_student",
            "has_dropped_out",
            "dropout_date",
            "dropout_reason",
            "trajectory_start_date",
            "trajectory_end_date",
            "has_diploma",
            "has_job_guarantee",
            "invoice_number",
            "invoice_sent_date",
            "invoice_paid_date",
            "invoice_status",
            "notes",
        ]
        widgets = {
            "is_active_student": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "has_dropped_out": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "dropout_date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"},
                format="%Y-%m-%d",
            ),
            "dropout_reason": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "trajectory_start_date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"},
                format="%Y-%m-%d",
            ),
            "trajectory_end_date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"},
                format="%Y-%m-%d",
            ),
            "has_diploma": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "has_job_guarantee": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "invoice_number": forms.TextInput(attrs={"class": "form-control"}),
            "invoice_sent_date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"},
                format="%Y-%m-%d",
            ),
            "invoice_paid_date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"},
                format="%Y-%m-%d",
            ),
            "invoice_status": forms.Select(attrs={"class": "form-select"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name in [
            "dropout_date",
            "trajectory_start_date",
            "trajectory_end_date",
            "invoice_sent_date",
            "invoice_paid_date",
        ]:
            self.fields[field_name].input_formats = ["%Y-%m-%d"]

    def clean(self):
        cleaned_data = super().clean()

        trajectory_start_date = cleaned_data.get("trajectory_start_date")
        trajectory_end_date = cleaned_data.get("trajectory_end_date")
        dropout_date = cleaned_data.get("dropout_date")
        invoice_sent_date = cleaned_data.get("invoice_sent_date")
        invoice_paid_date = cleaned_data.get("invoice_paid_date")

        if trajectory_start_date and trajectory_end_date and trajectory_end_date < trajectory_start_date:
            self.add_error(
                "trajectory_end_date",
                "De einddatum van het traject mag niet vóór de startdatum liggen.",
            )

        if invoice_sent_date and invoice_paid_date and invoice_paid_date < invoice_sent_date:
            self.add_error(
                "invoice_paid_date",
                "De betaaldatum mag niet vóór de verzenddatum liggen.",
            )

        if dropout_date:
            cleaned_data["has_dropped_out"] = True

        return cleaned_data