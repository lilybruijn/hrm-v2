from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from core.auth import staff_required
from core.models.history import HistoryEvent
from core.models.notes import Note
from core.models.people import Person
from .forms import PersonForm

from core.signals.services import log_history  # hergebruik jouw logger


@staff_required
def person_list(request):
    qs = Person.objects.all()

    q = (request.GET.get("q") or "").strip()
    person_type = (request.GET.get("type") or "").strip()  # student|employee|"" (alles)

    # sorting
    SORT_MAP = {
        "name": "last_name",
        "type": "person_type",
        "email": "email",
        "phone": "phone",
        "created_at": "created_at",
    }
    sort = (request.GET.get("sort") or "name").strip()
    dir_ = (request.GET.get("dir") or "asc").strip().lower()
    if dir_ not in ("asc", "desc"):
        dir_ = "asc"

    if q:
        qs = qs.filter(
            Q(first_name__icontains=q)
            | Q(last_name__icontains=q)
            | Q(email__icontains=q)
            | Q(phone__icontains=q)
        )

    if person_type in ("student", "employee"):
        qs = qs.filter(person_type=person_type)

    sort_field = SORT_MAP.get(sort, "last_name")
    prefix = "-" if dir_ == "desc" else ""
    qs = qs.order_by(f"{prefix}{sort_field}", "first_name", "id")

    paginator = Paginator(qs, 25)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(request, "core/people/list.html", {
        "page_obj": page_obj,
        "people": page_obj.object_list,
        "q": q,
        "person_type": person_type,
        "sort": sort,
        "dir": dir_,
        "type_choices": Person.PERSON_TYPE_CHOICES,
        "active_nav": "people",
    })


@staff_required
@transaction.atomic
def person_create(request):
    if request.method == "POST":
        form = PersonForm(request.POST)
        if form.is_valid():
            person = form.save()
            log_history(person, request.user, "created", {})
            messages.success(request, "Persoon aangemaakt.")
            return redirect("people:detail", pk=person.pk)
    else:
        form = PersonForm()

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

    history = (
        HistoryEvent.objects
        .select_related("actor")
        .filter(content_type=person_ct, object_id=person.pk)
        .order_by("-created_at")
    )

    ACTION_LABELS = {
        "created": "Persoon aangemaakt",
        "updated": "Persoon bijgewerkt",
        "note_added": "Notitie toegevoegd",
    }
    for h in history:
        h.action_label = ACTION_LABELS.get(h.action, h.action.replace("_", " ").capitalize())

    return render(request, "core/people/detail.html", {
        "person": person,
        "form": form,
        "notes": notes,
        "history": history,
        "active_nav": "people",
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
        "notes": person.notes,
    }

    form = PersonForm(request.POST, instance=person)
    if not form.is_valid():
        messages.error(request, "Formulier is niet geldig.")
        return redirect("people:detail", pk=person.pk)

    person = form.save()

    after = {
        "person_type": person.person_type,
        "first_name": person.first_name,
        "last_name": person.last_name,
        "email": person.email,
        "phone": person.phone,
        "notes": person.notes,
    }

    changes = {k: [before[k], after[k]] for k in before if before[k] != after[k]}
    if changes:
        log_history(person, request.user, "updated", changes)
        messages.success(request, "Persoon bijgewerkt.")

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