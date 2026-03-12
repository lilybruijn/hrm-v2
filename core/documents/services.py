def resolve_variable_value(variable, person=None, organization=None):
    if variable.source_type == "manual":
        return variable.default_value or ""

    if variable.source_type == "person" and person:
        return getattr(person, variable.source_path, "")

    if variable.source_type == "organization" and organization:
        return getattr(organization, variable.source_path, "")

    if variable.source_type == "student_profile" and hasattr(person, "student_profile"):
        profile = person.student_profile
        return getattr(profile, variable.source_path, "")

    if variable.source_type == "employee_profile" and hasattr(person, "employee_profile"):
        profile = person.employee_profile
        return getattr(profile, variable.source_path, "")

    return variable.default_value or ""
from io import BytesIO
from pathlib import Path

from django.core.files.base import ContentFile
from docxtpl import DocxTemplate


def build_nested_context(flat_data):
    context = {}

    for key, value in (flat_data or {}).items():
        if "." not in key:
            context[key] = value
            continue

        parts = key.split(".")
        current = context

        for part in parts[:-1]:
            if part not in current or not isinstance(current[part], dict):
                current[part] = {}
            current = current[part]

        current[parts[-1]] = value

    return context


def generate_docx_for_document(document):
    template_path = Path(document.template.template_file.path)

    if not template_path.exists():
        raise FileNotFoundError(f"Templatebestand niet gevonden: {template_path}")

    flat_context = document.rendered_data or {}
    context = build_nested_context(flat_context)

    doc = DocxTemplate(str(template_path))
    doc.render(context)

    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)

    safe_title = "".join(
        c for c in document.title if c.isalnum() or c in (" ", "-", "_")
    ).strip()
    safe_title = safe_title.replace(" ", "_") or f"document_{document.pk}"

    filename = f"{safe_title}.docx"

    document.file.save(filename, ContentFile(buffer.read()), save=False)
    document.status = "generated"
    document.save(update_fields=["file", "status"])

import re
import zipfile


PLACEHOLDER_PATTERN = re.compile(r"{{\s*([a-zA-Z0-9_\.]+)\s*}}")


def extract_docx_placeholders(file_path):
    placeholders = set()

    with zipfile.ZipFile(file_path, "r") as docx_zip:
        for name in docx_zip.namelist():
            if name.endswith(".xml"):
                content = docx_zip.read(name).decode("utf-8", errors="ignore")
                matches = PLACEHOLDER_PATTERN.findall(content)
                placeholders.update(matches)

    return sorted(placeholders)


from core.models import TemplateVariable


def guess_source_type_and_path(key):
    person_fields = {
        "first_name", "last_name", "full_name", "birth_date", "bsn",
        "email", "phone", "street", "house_number", "postal_code", "city",
    }
    organization_fields = {"name", "email", "phone", "street", "house_number", "postal_code", "city"}

    if key.startswith("person."):
        return "person", key.replace("person.", "", 1)

    if key.startswith("organization."):
        return "organization", key.replace("organization.", "", 1)

    if key.startswith("student_profile."):
        return "student_profile", key.replace("student_profile.", "", 1)

    if key.startswith("employee_profile."):
        return "employee_profile", key.replace("employee_profile.", "", 1)

    if key in person_fields:
        return "person", key

    if key in organization_fields:
        return "organization", key

    return "manual", ""


def humanize_key(key):
    label = key.replace(".", " ").replace("_", " ")
    return label[:1].upper() + label[1:]


def sync_template_variables_from_docx(template):
    if not template.template_file:
        return []

    placeholders = extract_docx_placeholders(template.template_file.path)
    created_variables = []

    existing_keys = set(template.variables.values_list("key", flat=True))

    next_sort_order = (
        template.variables.order_by("-sort_order").values_list("sort_order", flat=True).first() or 0
    )

    for placeholder in placeholders:
        if placeholder in existing_keys:
            continue

        source_type, source_path = guess_source_type_and_path(placeholder)
        next_sort_order += 1

        variable = TemplateVariable.objects.create(
            template=template,
            key=placeholder,
            label=humanize_key(placeholder),
            field_type="text",
            required=False,
            default_value="",
            source_type=source_type,
            source_path=source_path,
            help_text="Automatisch herkend uit template",
            sort_order=next_sort_order,
            is_archived=False,
        )
        created_variables.append(variable)

    return created_variables