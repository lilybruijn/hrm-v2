from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from core.auth import staff_required

from .forms import ContactPersonForm
from core.models import ContactPerson, Person, PersonContact, SettingOption


@staff_required
def contact_list(request):
    contacts = ContactPerson.objects.select_related("organization").order_by("last_name")

    return render(request, "core/contacts/list.html", {
        "contacts": contacts,
        "active_nav": "contacts",
    })


@staff_required
def contact_detail(request, pk: int):
    contact = get_object_or_404(
        ContactPerson.objects.select_related("organization").prefetch_related("linked_people__person"),
        pk=pk
    )

    return render(request, "core/contacts/detail.html", {
        "contact": contact,
        "active_nav": "contacts",
    })


@staff_required
def contact_create(request):
    person_id = (request.GET.get("person") or "").strip()

    if request.method == "POST":
        form = ContactPersonForm(request.POST)
        if form.is_valid():
            contact = form.save()

            if person_id.isdigit():
                person = get_object_or_404(Person, pk=int(person_id))
                default_relation_type = SettingOption.objects.filter(
                    category="person_contact_relation_type",
                    is_active=True,
                ).order_by("sort_order", "id").first()

                if default_relation_type:
                    PersonContact.objects.get_or_create(
                        person=person,
                        contact_person=contact,
                        relation_type=default_relation_type,
                        defaults={"is_primary": False},
                    )

            messages.success(request, "Contactpersoon aangemaakt.")
            return redirect("contacts:detail", pk=contact.pk)
    else:
        form = ContactPersonForm()

    return render(request, "core/contacts/form.html", {
        "form": form,
        "mode": "create",
        "active_nav": "contacts",
    })

@staff_required
def contact_update(request, pk: int):
    contact = get_object_or_404(ContactPerson, pk=pk)

    if request.method == "POST":
        form = ContactPersonForm(request.POST, instance=contact)
        if form.is_valid():
            contact = form.save()
            messages.success(request, "Contactpersoon bijgewerkt.")
            return redirect("contacts:detail", pk=contact.pk)
    else:
        form = ContactPersonForm(instance=contact)

    return render(request, "core/contacts/form.html", {
        "form": form,
        "mode": "update",
        "contact": contact,
        "active_nav": "contacts",
    })