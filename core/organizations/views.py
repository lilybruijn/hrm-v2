from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from core.auth import staff_required
from core.models import Organization
from core.organizations.forms import OrganizationForm


@staff_required
def organization_list(request):
    archived = (request.GET.get("archived") or "").strip()

    organizations = Organization.objects.select_related("organization_type")

    if archived == "1":
        organizations = organizations.filter(is_archived=True)
    elif archived == "0":
        organizations = organizations.filter(is_archived=False)

    organizations = organizations.order_by("name")

    return render(request, "core/organizations/list.html", {
        "organizations": organizations,
        "archived": archived,
        "active_nav": "organizations",
    })


@staff_required
def organization_create(request):
    if request.method == "POST":
        form = OrganizationForm(request.POST)
        if form.is_valid():
            organization = form.save()
            messages.success(request, "Organisatie aangemaakt.")
            return redirect("organizations:detail", pk=organization.pk)
    else:
        form = OrganizationForm()

    return render(request, "core/organizations/form.html", {
        "form": form,
        "mode": "create",
        "active_nav": "organizations",
    })


@staff_required
def organization_detail(request, pk: int):
    organization = get_object_or_404(
        Organization.objects.select_related("organization_type"),
        pk=pk
    )

    return render(request, "core/organizations/detail.html", {
        "organization": organization,
        "active_nav": "organizations",
    })


@staff_required
def organization_update(request, pk: int):
    organization = get_object_or_404(Organization, pk=pk)

    if request.method == "POST":
        form = OrganizationForm(request.POST, instance=organization)
        if form.is_valid():
            form.save()
            messages.success(request, "Organisatie bijgewerkt.")
            return redirect("organizations:detail", pk=organization.pk)
    else:
        form = OrganizationForm(instance=organization)

    return render(request, "core/organizations/form.html", {
        "form": form,
        "mode": "update",
        "organization": organization,
        "active_nav": "organizations",
    })


@staff_required
@require_POST
def organization_archive(request, pk: int):
    organization = get_object_or_404(Organization, pk=pk)
    organization.is_archived = True
    organization.save(update_fields=["is_archived"])
    messages.success(request, "Organisatie gearchiveerd.")
    return redirect("organizations:list")


@staff_required
@require_POST
def organization_restore(request, pk: int):
    organization = get_object_or_404(Organization, pk=pk)
    organization.is_archived = False
    organization.save(update_fields=["is_archived"])
    messages.success(request, "Organisatie hersteld.")
    return redirect("organizations:list")