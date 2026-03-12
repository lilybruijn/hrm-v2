from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from core.auth import staff_required
from core.models import DocumentTemplate, TemplateVariable, GeneratedDocument, Person
from .forms import DocumentTemplateForm, TemplateVariableForm, GeneratedDocumentCreateForm

from .services import resolve_variable_value, generate_docx_for_document

@staff_required
def template_list(request):
    templates = DocumentTemplate.objects.select_related("document_type")

    archived = (request.GET.get("archived") or "").strip()

    if archived == "1":
        templates = templates.filter(is_archived=True)
    elif archived == "0":
        templates = templates.filter(is_archived=False)

    templates = templates.order_by("name")

    return render(request, "core/documents/template_list.html", {
        "templates": templates,
        "archived": archived,
        "active_nav": "settings",
    })


@staff_required
def template_create(request):
    if request.method == "POST":
        form = DocumentTemplateForm(request.POST, request.FILES)
        if form.is_valid():
            template = form.save()
            messages.success(request, "Documentsjabloon aangemaakt.")
            return redirect("documents:template_detail", pk=template.pk)
    else:
        form = DocumentTemplateForm()

    return render(request, "core/documents/template_form.html", {
        "form": form,
        "mode": "create",
        "active_nav": "settings",
    })


@staff_required
def template_detail(request, pk: int):
    template = get_object_or_404(DocumentTemplate.objects.select_related("document_type"), pk=pk)
    variables = template.variables.all()

    return render(request, "core/documents/template_detail.html", {
        "template": template,
        "variables": variables,
        "active_nav": "settings",
    })


@staff_required
def template_variable_create(request, template_pk: int):
    template = get_object_or_404(DocumentTemplate, pk=template_pk)

    if request.method == "POST":
        form = TemplateVariableForm(request.POST)
        if form.is_valid():
            variable = form.save(commit=False)
            variable.template = template
            variable.save()
            messages.success(request, "Variabele toegevoegd.")
            return redirect("documents:template_detail", pk=template.pk)
    else:
        form = TemplateVariableForm()

    return render(request, "core/documents/template_variable_form.html", {
        "template": template,
        "form": form,
        "active_nav": "settings",
    })


@staff_required
def person_document_create(request, person_pk: int):
    person = get_object_or_404(Person, pk=person_pk)

    if request.method == "POST":
        form = GeneratedDocumentCreateForm(request.POST, person=person)
        if form.is_valid():
            document = form.save(commit=False)
            document.person = person
            document.generated_by = request.user
            document.status = "draft"

            if not document.title:
                document.title = f"{document.template.name} - {person.full_name}"

            document.save()

        messages.success(request, "Document aangemaakt.")
        return redirect("documents:document_variables", document.pk)
    else:
        form = GeneratedDocumentCreateForm(
            person=person,
            initial={"title": f"Nieuw document - {person.full_name}"}
        )

    return render(request, "core/documents/person_document_form.html", {
        "person": person,
        "form": form,
        "active_nav": "people",
    })

@staff_required
def person_document_variables(request, document_pk):
    document = get_object_or_404(GeneratedDocument, pk=document_pk)
    template = document.template
    person = document.person
    organization = document.organization

    variables = template.variables.filter(is_archived=False)

    if request.method == "POST":

        rendered_data = {}

        for var in variables:
            value = request.POST.get(var.key)

            if not value:
                value = resolve_variable_value(var, person, organization)

            rendered_data[var.key] = value

        document.rendered_data = rendered_data
        document.save(update_fields=["rendered_data"])

        generate_docx_for_document(document)

        messages.success(request, "Document gegenereerd.")
        return redirect("people:detail", pk=person.pk)


    variables = list(template.variables.filter(is_archived=False))

    for var in variables:
        var.resolved_value = resolve_variable_value(var, person, organization)

    return render(request, "core/documents/document_variables_form.html", {
        "document": document,
        "variables": variables,
        "person": person,
        "organization": organization,
        "active_nav": "people",
    })

@staff_required
@require_POST
def template_archive(request, pk: int):
    template = get_object_or_404(DocumentTemplate, pk=pk)
    template.is_archived = True
    template.save(update_fields=["is_archived"])

    messages.success(request, "Documentsjabloon gearchiveerd.")
    return redirect("documents:template_list")

@staff_required
@require_POST
def template_restore(request, pk: int):
    template = get_object_or_404(DocumentTemplate, pk=pk)
    template.is_archived = False
    template.save(update_fields=["is_archived"])

    messages.success(request, "Documentsjabloon hersteld.")
    return redirect("documents:template_list")

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST

@staff_required
@require_POST
def template_delete(request, pk: int):
    template = get_object_or_404(DocumentTemplate, pk=pk)

    generated_count = template.generated_documents.count()

    if generated_count > 0:
        messages.error(
            request,
            f"Dit documentsjabloon kan niet verwijderd worden omdat het al in {generated_count} document(en) is gebruikt. Archiveer het sjabloon in plaats daarvan."
        )
        return redirect("documents:template_list")

    template.delete()

    messages.success(request, "Documentsjabloon permanent verwijderd.")
    return redirect("documents:template_list")