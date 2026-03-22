from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST, require_http_methods
from django.template.loader import render_to_string
from django.http import HttpResponse
from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.utils import timezone

from core.auth import staff_required
from core.models.history import HistoryEvent
from core.models.notes import Note
from core.models.core import Signal, Task
from .forms import PersonForm
from core.signals.services import log_history
from .student_forms import StudentProfileForm
from core.models.people import Person, StudentProfile, EmployeeProfile

def get_person_history(person):
    person_ct = ContentType.objects.get_for_model(Person)

    history = (
        HistoryEvent.objects
        .select_related("actor")
        .filter(content_type=person_ct, object_id=person.pk)
        .order_by("-created_at")[:25]
    )

    action_labels = {
        "created": "Persoon aangemaakt",
        "updated": "Persoon bijgewerkt",
        "note_added": "Notitie toegevoegd",
    }

    for h in history:
        h.action_label = action_labels.get(h.action, h.action.replace("_", " ").capitalize())

    return history

@staff_required
def person_list(request):
    qs = Person.objects.all()
    q = (request.GET.get("q") or "").strip()
    archived = (request.GET.get("archived") or "").strip()

    if archived == "1":
        qs = qs.filter(is_archived=True)
    elif archived == "0":
        qs = qs.filter(is_archived=False)

    if q:
        parts = [part.strip() for part in q.split() if part.strip()]

        name_query = Q()
        for part in parts:
            name_query &= (
                Q(first_name__icontains=part) |
                Q(last_name__icontains=part)
            )

        qs = qs.filter(name_query | Q(email__icontains=q))

    qs = qs.order_by("last_name", "first_name")
    paginator = Paginator(qs, 25)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(request, "core/people/list.html", {
        "people": page_obj.object_list,
        "page_obj": page_obj,
        "q": q,
        "archived": archived,
        "active_nav": "people",
    })

@staff_required
def student_list(request):
    qs = (
        Person.objects
        .filter(person_type="student", is_archived=False)
        .select_related("student_profile")
    )

    q = (request.GET.get("q") or "").strip()
    status = (request.GET.get("status") or "").strip()
    sort = (request.GET.get("sort") or "name").strip()
    direction = (request.GET.get("dir") or "asc").strip()

    if q:
        parts = [part.strip() for part in q.split() if part.strip()]

        name_query = Q()
        for part in parts:
            name_query &= (
                Q(first_name__icontains=part) |
                Q(last_name__icontains=part)
            )

        qs = qs.filter(
            name_query |
            Q(email__icontains=q) |
            Q(phone__icontains=q)
        )

    if status == "active":
        qs = qs.filter(student_profile__is_active_student=True, student_profile__has_dropped_out=False)
    elif status == "dropped_out":
        qs = qs.filter(student_profile__has_dropped_out=True)
    elif status == "almost_finished":
        today = timezone.localdate()
        soon = today + timedelta(days=30)
        qs = qs.filter(
            student_profile__has_dropped_out=False,
            student_profile__trajectory_end_date__isnull=False,
            student_profile__trajectory_end_date__gte=today,
            student_profile__trajectory_end_date__lte=soon,
        )

    sort_map = {
        "id": "id",
        "name": "last_name",
        "status": "student_profile__has_dropped_out",
        "trajectory_end": "student_profile__trajectory_end_date",
        "diploma": "student_profile__has_diploma",
        "invoice_status": "student_profile__invoice_status",
        "created_at": "created_at",
    }

    order_field = sort_map.get(sort, "last_name")
    if direction == "desc":
        order_field = f"-{order_field}"

    qs = qs.order_by(order_field, "last_name", "first_name")

    return render(request, "core/people/student_list.html", {
        "people": qs,
        "q": q,
        "status": status,
        "sort": sort,
        "dir": direction,
        "active_nav": "people_students",
    })

@staff_required
def employee_list(request):
    qs = (
        Person.objects
        .filter(person_type="employee", is_archived=False)
    )

    q = (request.GET.get("q") or "").strip()
    sort = (request.GET.get("sort") or "name").strip()
    direction = (request.GET.get("dir") or "asc").strip()

    if q:
        parts = [part.strip() for part in q.split() if part.strip()]

        name_query = Q()
        for part in parts:
            name_query &= (
                Q(first_name__icontains=part) |
                Q(last_name__icontains=part)
            )

        qs = qs.filter(
            name_query |
            Q(email__icontains=q) |
            Q(phone__icontains=q)
        )

    sort_map = {
        "id": "id",
        "name": "last_name",
        "email": "email",
        "phone": "phone",
        "created_at": "created_at",
    }

    order_field = sort_map.get(sort, "last_name")
    if direction == "desc":
        order_field = f"-{order_field}"

    qs = qs.order_by(order_field, "last_name", "first_name")

    return render(request, "core/people/employee_list.html", {
        "people": qs,
        "q": q,
        "sort": sort,
        "dir": direction,
        "active_nav": "people_employees",
    })

@staff_required
def archived_list(request):
    qs = (
        Person.objects
        .filter(is_archived=True)
        .select_related("student_profile")
    )

    q = (request.GET.get("q") or "").strip()
    person_type = (request.GET.get("type") or "").strip()
    sort = (request.GET.get("sort") or "name").strip()
    direction = (request.GET.get("dir") or "asc").strip()

    if q:
        parts = [part.strip() for part in q.split() if part.strip()]

        name_query = Q()
        for part in parts:
            name_query &= (
                Q(first_name__icontains=part) |
                Q(last_name__icontains=part)
            )

        qs = qs.filter(
            name_query |
            Q(email__icontains=q) |
            Q(phone__icontains=q)
        )

    if person_type:
        qs = qs.filter(person_type=person_type)

    sort_map = {
        "id": "id",
        "name": "last_name",
        "type": "person_type",
        "email": "email",
        "phone": "phone",
        "created_at": "created_at",
    }

    order_field = sort_map.get(sort, "last_name")
    if direction == "desc":
        order_field = f"-{order_field}"

    qs = qs.order_by(order_field, "last_name", "first_name")

    return render(request, "core/people/archived_list.html", {
        "people": qs,
        "q": q,
        "person_type": person_type,
        "sort": sort,
        "dir": direction,
        "active_nav": "people_archived",
    })

@staff_required
def person_create(request):
    initial = {}
    requested_type = (request.GET.get("type") or "").strip()

    if requested_type in ["student", "employee"]:
        initial["person_type"] = requested_type

    if request.method == "POST":
        form = PersonForm(request.POST)
        if form.is_valid():
            person = form.save()

            if person.person_type == "student":
                StudentProfile.objects.get_or_create(person=person)
            elif person.person_type == "employee":
                EmployeeProfile.objects.get_or_create(person=person)

            log_history(person, request.user, "created", {})
            messages.success(request, "Persoon aangemaakt.")
            return redirect("people:detail", pk=person.pk)
    else:
        form = PersonForm(initial=initial)

    return render(request, "core/people/form.html", {
        "form": form,
        "mode": "create",
        "active_nav": "people",
    })

@staff_required
def person_detail(request, pk: int):
    person = get_object_or_404(Person, pk=pk)
    form = PersonForm(instance=person)

    person_ct = ContentType.objects.get_for_model(Person)

    notes = (
        Note.objects
        .select_related("author")
        .filter(content_type=person_ct, object_id=person.pk)
        .order_by("-created_at")
    )
    contact_links = person.person_contacts.select_related(
        "contact_person",
        "relation_type",
        "contact_person__organization",
    )
    history = get_person_history(person)

    ACTION_LABELS = {
        "created": "Persoon aangemaakt",
        "updated": "Persoon bijgewerkt",
        "note_added": "Notitie toegevoegd",
    }
    for h in history:
        h.action_label = ACTION_LABELS.get(h.action, h.action.replace("_", " ").capitalize())

    signals = (
        Signal.objects
        .select_related("type", "status", "assigned_to")
        .filter(people=person)
        .distinct()
        .order_by("-created_at")[:10]
    )

    tasks = (
        Task.objects
        .select_related("type", "status", "assigned_to", "signal")
        .filter(people=person, is_archived=False)
        .distinct()
        .order_by("due_at", "-created_at")[:10]
    )

    student_profile = getattr(person, "student_profile", None)
    employee_profile = getattr(person, "employee_profile", None)


    return render(request, "core/people/detail.html", {
        "person": person,
        "form": form,
        "signals": signals,
        "tasks": tasks,
        "notes": notes,
        "history": history,
        "active_nav": "people",
        "student_profile": student_profile,
        "employee_profile": employee_profile,
      
        "contact_links": contact_links,
    })


@staff_required
@transaction.atomic
def person_update(request, pk: int):
    person = get_object_or_404(Person, pk=pk)

    if request.method != "POST":
        return redirect("people:detail", pk=person.pk)

    before = {
        "person_type": person.person_type,
        "first_name": person.first_name,
        "last_name": person.last_name,
        "email": person.email,
        "phone": person.phone,
    }

    form = PersonForm(request.POST, instance=person)

    if not form.is_valid():
        messages.error(request, "Formulier is niet geldig.")
        person_ct = ContentType.objects.get_for_model(Person)
        notes = (
            Note.objects
            .select_related("author")
            .filter(content_type=person_ct, object_id=person.pk)
            .order_by("-created_at")
        )
        contact_links = person.person_contacts.select_related(
            "contact_person",
            "relation_type",
            "contact_person__organization",
        )
        history = get_person_history(person)

        signals = (
            Signal.objects
            .select_related("type", "status", "assigned_to")
            .filter(people=person)
            .distinct()
            .order_by("-created_at")[:10]
        )

        tasks = (
            Task.objects
            .select_related("type", "status", "assigned_to", "signal")
            .filter(people=person, is_archived=False)
            .distinct()
            .order_by("due_at", "-created_at")[:10]
        )

        return render(request, "core/people/detail.html", {
            "person": person,
            "form": form,
            "signals": signals,
            "tasks": tasks,
            "notes": notes,
            "history": history,
            "active_nav": "people",
            "student_profile": getattr(person, "student_profile", None),
            "employee_profile": getattr(person, "employee_profile", None),
            "contact_links": contact_links,
        })

    person = form.save()
    if person.person_type == "student":
        StudentProfile.objects.get_or_create(person=person)
    elif person.person_type == "employee":
        EmployeeProfile.objects.get_or_create(person=person)
        
    after = {
        "person_type": person.person_type,
        "first_name": person.first_name,
        "last_name": person.last_name,
        "email": person.email,
        "phone": person.phone,
    }

    changes = {k: [before[k], after[k]] for k in before if before[k] != after[k]}
    if changes:
        log_history(person, request.user, "updated", changes)

    messages.success(request, "Persoon bijgewerkt.")
    return redirect("people:detail", pk=person.pk)


@staff_required
@require_POST
@transaction.atomic
def person_update_description(request, pk: int):
    person = get_object_or_404(Person, pk=pk)

    new_description = (request.POST.get("description") or "").strip()
    old_description = person.description or ""

    if new_description != old_description:
        person.description = new_description
        person.save(update_fields=["description"])
        log_history(
            person,
            request.user,
            "updated",
            {"description": [old_description, new_description]},
        )
        messages.success(request, "Omschrijving bijgewerkt.")

    return redirect("people:detail", pk=person.pk)


@staff_required
@require_POST
@transaction.atomic
def person_add_note(request, pk: int):
    person = get_object_or_404(Person, pk=pk)
    body = (request.POST.get("body") or "").strip()

    if not body:
        messages.error(request, "Notitie is leeg.")
        return redirect("people:detail", pk=person.pk)

    note = Note.objects.create(
        author=request.user,
        body=body,
        content_object=person
    )
    log_history(person, request.user, "note_added", {"note_id": [None, note.id]})
    messages.success(request, "Notitie toegevoegd.")
    return redirect("people:detail", pk=person.pk)


@staff_required
@require_POST
@transaction.atomic
def person_toggle_archive(request, pk: int):
    person = get_object_or_404(Person, pk=pk)

    person.is_archived = not person.is_archived
    person.save(update_fields=["is_archived"])

    messages.success(request, "Archiefstatus bijgewerkt.")
    return redirect("people:list")


@staff_required
@require_POST
@transaction.atomic
def person_toggle_archive_detail(request, pk: int):
    person = get_object_or_404(Person, pk=pk)

    person.is_archived = not person.is_archived
    person.save(update_fields=["is_archived"])

    messages.success(request, "Archiefstatus bijgewerkt.")
    return redirect("people:detail", pk=person.pk)


@staff_required
@require_POST
@transaction.atomic
def person_restore(request, pk: int):
    person = get_object_or_404(Person, pk=pk)

    if person.is_archived:
        person.is_archived = False
        person.save(update_fields=["is_archived"])
        messages.success(request, "Persoon hersteld.")

    return redirect("people:list")


@staff_required
@require_POST
@transaction.atomic
def person_delete(request, pk: int):
    person = get_object_or_404(Person, pk=pk)

    if not person.is_archived:
        messages.error(request, "Archiveer de persoon eerst voordat je deze permanent verwijdert.")
        return redirect("people:list")

    has_signals = person.signals.exists()
    has_tasks = person.tasks.exists()

    if has_signals or has_tasks:
        messages.error(request, "Deze persoon is nog gekoppeld aan meldingen of taken.")
        return redirect("people:list")

    person.delete()
    messages.success(request, "Persoon permanent verwijderd.")
    return redirect("people:list")

@staff_required
@require_http_methods(["GET"])
def person_description_view_partial(request, pk: int):
    person = get_object_or_404(Person, pk=pk)

    return render(request, "core/people/partials/person_description_view.html", {
        "person": person,
    })

@staff_required
@require_http_methods(["GET", "POST"])
def person_description_edit_partial(request, pk: int):
    person = get_object_or_404(Person, pk=pk)

    if request.method == "POST":
        old_description = person.description or ""
        new_description = (request.POST.get("description") or "").strip()

        if new_description != old_description:
            person.description = new_description
            person.save(update_fields=["description"])

            log_history(
                person,
                request.user,
                "updated",
                {"description": [old_description, new_description]},
            )

        history = get_person_history(person)

        return render(request, "core/people/partials/person_description_response.html", {
            "person": person,
            "history": history,
        })

    return render(request, "core/people/partials/person_description_edit.html", {
        "person": person,
    })

@staff_required
@require_http_methods(["GET"])
def person_data_view_partial(request, pk: int):
    person = get_object_or_404(Person, pk=pk)

    return render(request, "core/people/partials/person_data_view.html", {
        "person": person,
        "student_profile": getattr(person, "student_profile", None),
        "employee_profile": getattr(person, "employee_profile", None),
    })

@staff_required
@require_http_methods(["GET", "POST"])
def person_data_edit_partial(request, pk: int):
    person = get_object_or_404(Person, pk=pk)

    if request.method == "POST":
        before = {
            "person_type": person.person_type,
            "first_name": person.first_name,
            "last_name": person.last_name,
            "birth_date": person.birth_date,
            "bsn": person.bsn,
            "email": person.email,
            "phone": person.phone,
            "street": person.street,
            "house_number": person.house_number,
            "postal_code": person.postal_code,
            "city": person.city,
        }

        form = PersonForm(request.POST, instance=person)

        if form.is_valid():
            person = form.save()

            if person.person_type == "student":
                StudentProfile.objects.get_or_create(person=person)
            elif person.person_type == "employee":
                EmployeeProfile.objects.get_or_create(person=person)

            after = {
                "person_type": person.person_type,
                "first_name": person.first_name,
                "last_name": person.last_name,
                "birth_date": person.birth_date,
                "bsn": person.bsn,
                "email": person.email,
                "phone": person.phone,
                "street": person.street,
                "house_number": person.house_number,
                "postal_code": person.postal_code,
                "city": person.city,
            }

            changes = {k: [before[k], after[k]] for k in before if before[k] != after[k]}
            if changes:
                log_history(person, request.user, "updated", changes)

            history = get_person_history(person)

            return render(request, "core/people/partials/person_data_response.html", {
                "person": person,
                "student_profile": getattr(person, "student_profile", None),
                "employee_profile": getattr(person, "employee_profile", None),
                "history": history,
            })

        return render(request, "core/people/partials/person_data_edit.html", {
            "person": person,
            "form": form,
            "student_profile": getattr(person, "student_profile", None),
            "employee_profile": getattr(person, "employee_profile", None),
        })

    form = PersonForm(instance=person)
    return render(request, "core/people/partials/person_data_edit.html", {
        "person": person,
        "form": form,
        "student_profile": getattr(person, "student_profile", None),
        "employee_profile": getattr(person, "employee_profile", None),
    })

@staff_required
@require_http_methods(["GET"])
def person_history_partial(request, pk: int):
    person = get_object_or_404(Person, pk=pk)
    history = get_person_history(person)

    return render(request, "core/people/partials/person_history.html", {
        "person": person,
        "history": history,
    })

@staff_required
@require_http_methods(["GET"])
def person_student_profile_view_partial(request, pk: int):
    person = get_object_or_404(Person, pk=pk)
    student_profile = getattr(person, "student_profile", None)
    return render(request, "core/people/partials/person_student_profile_view.html", {
        "person": person,
        "student_profile": student_profile,
    })


@staff_required
@require_http_methods(["GET", "POST"])
def person_student_profile_edit_partial(request, pk: int):
    person = get_object_or_404(Person, pk=pk)
    student_profile, _ = StudentProfile.objects.get_or_create(person=person)

    if request.method == "POST":
        form = StudentProfileForm(request.POST, instance=student_profile)

        if form.is_valid():
            form.save()

            return render(request, "core/people/partials/person_student_profile_view.html", {
                "person": person,
                "student_profile": person.student_profile,
            })

        return render(request, "core/people/partials/person_student_profile_edit.html", {
            "person": person,
            "student_profile": student_profile,
            "form": form,
        })

    form = StudentProfileForm(instance=student_profile)
    return render(request, "core/people/partials/person_student_profile_edit.html", {
        "person": person,
        "student_profile": student_profile,
        "form": form,
    })