from django import forms
from core.models import DocumentTemplate, TemplateVariable, GeneratedDocument, SettingOption, Organization


class DocumentTemplateForm(forms.ModelForm):
    class Meta:
        model = DocumentTemplate
        fields = [
            "name",
            "document_type",
            "target_type",
            "output_format",
            "template_file",
            "description",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "document_type": forms.Select(attrs={"class": "form-select"}),
            "target_type": forms.Select(attrs={"class": "form-select"}),
            "output_format": forms.Select(attrs={"class": "form-select"}),
            "template_file": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["document_type"].queryset = SettingOption.objects.filter(
            category="document_type",
        ).order_by("sort_order", "label")


class TemplateVariableForm(forms.ModelForm):
    class Meta:
        model = TemplateVariable
        fields = [
            "key",
            "label",
            "field_type",
            "required",
            "default_value",
            "source_type",
            "source_path",
            "help_text",
            "sort_order",
        ]
        widgets = {
            "key": forms.TextInput(attrs={"class": "form-control"}),
            "label": forms.TextInput(attrs={"class": "form-control"}),
            "field_type": forms.Select(attrs={"class": "form-select"}),
            "required": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "default_value": forms.TextInput(attrs={"class": "form-control"}),
            "source_type": forms.Select(attrs={"class": "form-select"}),
            "source_path": forms.TextInput(attrs={"class": "form-control"}),
            "help_text": forms.TextInput(attrs={"class": "form-control"}),
            "sort_order": forms.NumberInput(attrs={"class": "form-control"}),
        }


class GeneratedDocumentCreateForm(forms.ModelForm):
    class Meta:
        model = GeneratedDocument
        fields = ["template", "organization", "title"]
        widgets = {
            "template": forms.Select(attrs={"class": "form-select"}),
            "organization": forms.Select(attrs={"class": "form-select js-select"}),
            "title": forms.TextInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        person = kwargs.pop("person", None)
        super().__init__(*args, **kwargs)

        self.fields["template"].queryset = DocumentTemplate.objects.filter(is_archived=False)

        if person:
            if getattr(person, "person_type", None) == "student":
                self.fields["template"].queryset = self.fields["template"].queryset.filter(
                    target_type__in=["student", "both"]
                )
            elif getattr(person, "person_type", None) == "employee":
                self.fields["template"].queryset = self.fields["template"].queryset.filter(
                    target_type__in=["employee", "both"]
                )

        self.fields["template"].queryset = DocumentTemplate.objects.filter(is_archived=False)