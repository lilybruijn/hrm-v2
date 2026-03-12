from django.conf import settings
from django.db import models


class DocumentTemplate(models.Model):
    TARGET_TYPE_CHOICES = [
        ("student", "Student"),
        ("employee", "Medewerker"),
        ("both", "Beide"),
    ]

    OUTPUT_FORMAT_CHOICES = [
        ("docx", "DOCX"),
        ("pdf", "PDF"),
    ]

    name = models.CharField(max_length=255)
    document_type = models.ForeignKey(
        "SettingOption",
        on_delete=models.PROTECT,
        related_name="document_templates",
        limit_choices_to={"category": "document_type"},
    )
    target_type = models.CharField(max_length=20, choices=TARGET_TYPE_CHOICES, default="both")
    output_format = models.CharField(max_length=10, choices=OUTPUT_FORMAT_CHOICES, default="docx")

    template_file = models.FileField(upload_to="document_templates/")
    description = models.TextField(blank=True)

    is_archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class TemplateVariable(models.Model):
    FIELD_TYPE_CHOICES = [
        ("text", "Tekst"),
        ("textarea", "Lange tekst"),
        ("date", "Datum"),
        ("number", "Nummer"),
        ("boolean", "Ja/Nee"),
    ]

    SOURCE_TYPE_CHOICES = [
        ("manual", "Handmatig"),
        ("person", "Persoon"),
        ("organization", "Organisatie"),
        ("student_profile", "Studentprofiel"),
        ("employee_profile", "Medewerkerprofiel"),
    ]

    template = models.ForeignKey(
        "DocumentTemplate",
        on_delete=models.CASCADE,
        related_name="variables",
    )
    key = models.CharField(max_length=100)
    label = models.CharField(max_length=255)
    field_type = models.CharField(max_length=20, choices=FIELD_TYPE_CHOICES, default="text")

    required = models.BooleanField(default=False)
    default_value = models.CharField(max_length=255, blank=True)

    source_type = models.CharField(max_length=30, choices=SOURCE_TYPE_CHOICES, default="manual")
    source_path = models.CharField(
        max_length=255,
        blank=True,
        help_text="Bijv. first_name, full_name, birth_date, name",
    )

    help_text = models.CharField(max_length=255, blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_archived = models.BooleanField(default=False)

    class Meta:
        ordering = ["sort_order", "label"]
        unique_together = ("template", "key")

    def __str__(self):
        return f"{self.template.name} - {self.label}"


class GeneratedDocument(models.Model):
    STATUS_CHOICES = [
        ("draft", "Concept"),
        ("generated", "Gegenereerd"),
        ("archived", "Gearchiveerd"),
    ]

    person = models.ForeignKey(
        "Person",
        on_delete=models.CASCADE,
        related_name="generated_documents",
    )
    template = models.ForeignKey(
        "DocumentTemplate",
        on_delete=models.PROTECT,
        related_name="generated_documents",
    )
    organization = models.ForeignKey(
        "Organization",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="generated_documents",
    )

    title = models.CharField(max_length=255)
    file = models.FileField(upload_to="generated_documents/", blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")

    rendered_data = models.JSONField(default=dict, blank=True)

    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="generated_documents",
    )
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-generated_at"]

    def __str__(self):
        return self.title