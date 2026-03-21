from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from datetime import timedelta
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.views.decorators.http import require_POST

from core.auth import staff_required
from core.models.people import Person
from core.models.notes import Note
from core.models.status import Status
from core.models.types import SignalType
from core.models.core import Signal, Task
from .forms import SignalForm, NoteForm
from .services import log_history, create_signal_notifications

User = get_user_model()

ACTION_LABELS = {
    "name": "Naam gewijzigd",
    "created": "Melding aangemaakt",
    "updated": "Melding bijgewerkt",
    "status_changed": "Status gewijzigd",
    "type_changed": "Type gewijzigd",
    "active_from_changed": "Actief vanaf aangepast",
    "reassigned": "Toewijzing gewijzigd",
    "archived_toggled": "Archiefstatus gewijzigd",
    "note_added": "Notitie toegevoegd",
}


@staff_required
def signal_list(request):
    qs = Signal.objects.select_related(
        "type",
        "status",
        "assigned_to",
        "assigned_by",
    ).prefetch_related("people")

    signal_q = (request.GET.get("signal_q") or "").strip()
    status_id = (request.GET.get("signal_status") or "").strip()
    type_id = (request.GET.get("signal_type") or "").strip()
    assignee_id = (request.GET.get("signal_assignee") or "").strip()
    person_id = (request.GET.get("signal_person") or "").strip()
    archived = (request.GET.get("archived") or "").strip()

    if archived == "1":
        qs = qs.filter(is_archived=True)
    elif archived == "0":
        qs = qs.filter(is_archived=False)

    if person_id.isdigit():
        qs = qs.filter(people__id=int(person_id)).distinct()

    if assignee_id == "unassigned":
        qs = qs.filter(assigned_to__isnull=True)
    elif assignee_id.isdigit():
        qs = qs.filter(assigned_to_id=int(assignee_id))

    if status_id.isdigit():
        qs = qs.filter(status_id=int(status_id))

    if type_id.isdigit():
        qs = qs.filter(type_id=int(type_id))

    if signal_q:
        qs = qs.filter(
            Q(name__icontains=signal_q)
            | Q(body__icontains=signal_q)
            | Q(assigned_to__username__icontains=signal_q)
        )

    SORT_MAP = {
        "id": "id",
        "name": "name",
        "active_from": "active_from",
        "type": "type__name",
        "status": "status__name",
        "assigned_to": "assigned_to__username",
        "created_at": "created_at",
    }

    sort = (request.GET.get("sort") or "active_from").strip()
    dir_ = (request.GET.get("dir") or "desc").strip().lower()

    if dir_ not in ("asc", "desc"):
        dir_ = "desc"

    sort_field = SORT_MAP.get(sort, "active_from")
    prefix = "-" if dir_ == "desc" else ""

    qs = qs.order_by(f"{prefix}{sort_field}", "-active_from", "-created_at").distinct()

    paginator = Paginator(qs, 25)
    page_obj = paginator.get_page(request.GET.get("page"))

    statuses = Status.objects.filter(scope="signal", is_active=True).order_by("sort_order", "name")
    types = SignalType.objects.filter(is_active=True).order_by("sort_order", "name")
    people = Person.objects.order_by("last_name", "first_name")

    assignees = (
        User.objects
        .filter(assigned_signals__isnull=False, is_staff=True, is_active=True)
        .distinct()
        .order_by("username")
    )

    return render(request, "core/signals/list.html", {
        "page_obj": page_obj,
        "signals": page_obj.object_list,
        "signal_q": signal_q,
        "status_id": status_id,
        "type_id": type_id,
        "person_id": person_id,
        "assignee_id": assignee_id,
        "assignees": assignees,
        "archived": archived,
        "statuses": statuses,
        "types": types,
        "people": people,
        "sort": sort,
        "dir": dir_,
        "active_nav": "signals",
    })


@staff_required
@require_POST
@transaction.atomic
def signal_delete(request, pk: int):
    signal = get_object_or_404(Signal, pk=pk)

    if not signal.is_archived:
        messages.error(request, "Archiveer de melding eerst voordat je deze permanent verwijdert.")
        return redirect("signals:list")

    signal.delete()
    messages.success(request, "Melding permanent verwijderd.")
    return redirect("signals:list")


@staff_required
@require_POST
@transaction.atomic
def signal_restore(request, pk: int):
    signal = get_object_or_404(Signal, pk=pk)

    if signal.is_archived:
        signal.is_archived = False
        signal.save(update_fields=["is_archived"])
        messages.success(request, "Melding hersteld.")

    return redirect("signals:list")


@staff_required
@transaction.atomic
def signal_create(request):
    people_param = (request.GET.get("people") or "").strip()
    assigned_to_id = (request.GET.get("assigned_to") or "").strip()

    if request.method == "POST":
        form = SignalForm(request.POST)
        if form.is_valid():
            signal = form.save(commit=False)

            if signal.assigned_to:
                signal.assigned_by = request.user

            signal.save()
            form.save_m2m()

            log_history(signal, request.user, "created", {})
            create_signal_notifications(signal, request.user)

            messages.success(request, "Melding aangemaakt.")
            return redirect("signals:detail", pk=signal.id)
    else:
        initial = {"active_from": timezone.localdate()}

        if people_param:
            ids = [int(x) for x in people_param.split(",") if x.strip().isdigit()]
            initial["people"] = ids
        
        if assigned_to_id.isdigit():
            initial["assigned_to"] = int(assigned_to_id)

        form = SignalForm(initial=initial)

    return render(request, "core/signals/form.html", {
        "form": form,
        "mode": "create",
        "active_nav": "signals",
    })


@staff_required
def signal_detail(request, pk: int):
    signal = get_object_or_404(
        Signal.objects.select_related(
            "type",
            "status",
            "assigned_to",
            "assigned_by",
        ).prefetch_related("people"),
        pk=pk,
    )

    form = SignalForm(instance=signal)
    note_form = NoteForm()

    notes = signal.notes.select_related("author").all()[:25]
    history = signal.history.select_related("actor").all()[:25]

    status_map = {s.id: s.name for s in Status.objects.filter(scope="signal")}
    type_map = {t.id: t.name for t in SignalType.objects.all()}
    user_map = {u.id: u.username for u in User.objects.all()}
    person_map = {p.id: f"{p.first_name} {p.last_name}" for p in Person.objects.all()}

    for h in history:
        h.action_label = ACTION_LABELS.get(h.action, h.action.replace("_", " ").capitalize())

    tasks = (
        Task.objects
        .select_related("type", "status", "assigned_to", "signal")
        .prefetch_related("people")
        .filter(signal=signal, is_archived=False)
        .order_by("due_at", "-created_at")
    )

    return render(request, "core/signals/detail.html", {
        "signal": signal,
        "form": form,
        "note_form": note_form,
        "tasks": tasks,
        "notes": notes,
        "history": history,
        "active_nav": "signals",
        "status_map": status_map,
        "type_map": type_map,
        "user_map": user_map,
        "person_map": person_map,
    })


@staff_required
@transaction.atomic
def signal_update(request, pk: int):
    signal = get_object_or_404(
        Signal.objects.select_related(
            "type",
            "status",
            "assigned_to",
            "assigned_by",
        ).prefetch_related("people"),
        pk=pk,
    )

    if request.method != "POST":
        return redirect("signals:detail", pk=signal.pk)

    old_assigned_to_id = signal.assigned_to_id

    before = {
        "name": signal.name,
        "type_id": signal.type_id,
        "assigned_to_id": signal.assigned_to_id,
        "status_id": signal.status_id,
        "active_from": signal.active_from.isoformat() if signal.active_from else None,
        "body": signal.body,
        "is_archived": signal.is_archived,
    }
    before_people = list(signal.people.values_list("id", flat=True))

    data = request.POST.copy()
    expected_fields = ["name", "type", "active_from", "status", "assigned_to", "body"]

    for f in expected_fields:
        if f not in data:
            if f in ("type", "status", "assigned_to"):
                data[f] = str(getattr(signal, f"{f}_id") or "")
            elif f == "active_from":
                data[f] = signal.active_from.isoformat() if signal.active_from else ""
            else:
                data[f] = getattr(signal, f) or ""

    form = SignalForm(data, instance=signal)

    if not form.is_valid():
        messages.error(request, "Formulier is niet geldig.")

        note_form = NoteForm()
        notes = signal.notes.select_related("author").all()
        history = signal.history.select_related("actor").all()[:25]
        tasks = (
            Task.objects
            .select_related("type", "status", "assigned_to", "signal")
            .prefetch_related("people")
            .filter(signal=signal, is_archived=False)
            .order_by("due_at", "-created_at")
        )

        status_map = {s.id: s.name for s in Status.objects.filter(scope="signal")}
        type_map = {t.id: t.name for t in SignalType.objects.all()}
        user_map = {u.id: u.username for u in User.objects.all()}
        person_map = {p.id: f"{p.first_name} {p.last_name}" for p in Person.objects.all()}

        for h in history:
            h.action_label = ACTION_LABELS.get(h.action, h.action.replace("_", " ").capitalize())

        return render(request, "core/signals/detail.html", {
            "signal": signal,
            "form": form,
            "note_form": note_form,
            "tasks": tasks,
            "notes": notes,
            "history": history,
            "active_nav": "signals",
            "status_map": status_map,
            "type_map": type_map,
            "user_map": user_map,
            "person_map": person_map,
        })

    signal = form.save(commit=False)

    assignment_changed = signal.assigned_to_id != old_assigned_to_id
    if assignment_changed and signal.assigned_to:
        signal.assigned_by = request.user

    signal.save()
    form.save_m2m()

    after_people = list(signal.people.values_list("id", flat=True))

    after = {
        "name": signal.name,
        "type_id": signal.type_id,
        "assigned_to_id": signal.assigned_to_id,
        "status_id": signal.status_id,
        "active_from": signal.active_from.isoformat() if signal.active_from else None,
        "body": signal.body,
        "is_archived": signal.is_archived,
    }

    changes = {k: [before[k], after[k]] for k in before if before[k] != after[k]}
    if before_people != after_people:
        changes["people"] = [before_people, after_people]

    if changes:
        log_history(signal, request.user, "updated", changes)

        if assignment_changed and signal.assigned_to:
            create_signal_notifications(signal, request.user)

        messages.success(request, "Melding bijgewerkt.")

    return redirect("signals:detail", pk=signal.pk)


@staff_required
@require_POST
@transaction.atomic
def signal_update_body(request, pk: int):
    signal = get_object_or_404(Signal, pk=pk)

    new_body = (request.POST.get("body") or "").strip()
    if not new_body:
        messages.error(request, "Omschrijving mag niet leeg zijn.")
        return redirect("signals:detail", pk=signal.pk)

    old_body = signal.body
    if old_body != new_body:
        signal.body = new_body
        signal.save(update_fields=["body"])
        log_history(signal, request.user, "updated", {"body": [old_body, new_body]})
        messages.success(request, "Omschrijving bijgewerkt.")

    return redirect("signals:detail", pk=signal.pk)


@staff_required
@require_POST
@transaction.atomic
def signal_add_note(request, pk: int):
    signal = get_object_or_404(Signal, pk=pk)

    form = NoteForm(request.POST)
    if form.is_valid():
        note: Note = form.save(commit=False)
        note.author = request.user
        note.content_object = signal
        note.save()
        log_history(signal, request.user, "note_added", {"note_id": [None, note.id]})
        messages.success(request, "Notitie toegevoegd.")
    else:
        messages.error(request, "Notitie is leeg/ongeldig.")

    return redirect("signals:detail", pk=signal.pk)


@staff_required
@require_POST
@transaction.atomic
def signal_set_status(request, pk: int):
    signal = get_object_or_404(Signal, pk=pk)
    status_id = (request.POST.get("status_id") or "").strip()

    if not status_id.isdigit():
        messages.error(request, "Ongeldige status.")
        return redirect("signals:detail", pk=signal.pk)

    new_status = get_object_or_404(Status, pk=int(status_id), scope="signal")

    old = signal.status_id
    if old != new_status.id:
        signal.status = new_status
        signal.save(update_fields=["status"])
        log_history(signal, request.user, "status_changed", {"status_id": [old, new_status.id]})
        messages.success(request, "Status bijgewerkt.")

    return redirect("signals:detail", pk=signal.pk)


@staff_required
@require_POST
@transaction.atomic
def signal_set_type(request, pk: int):
    signal = get_object_or_404(Signal, pk=pk)
    type_id = (request.POST.get("type_id") or "").strip()

    if not type_id.isdigit():
        messages.error(request, "Ongeldig type.")
        return redirect("signals:detail", pk=signal.pk)

    new_type = get_object_or_404(SignalType, pk=int(type_id))

    old = signal.type_id
    if old != new_type.id:
        signal.type = new_type
        signal.save(update_fields=["type"])
        log_history(signal, request.user, "type_changed", {"type_id": [old, new_type.id]})
        messages.success(request, "Type bijgewerkt.")

    return redirect("signals:detail", pk=signal.pk)


@staff_required
@require_POST
@transaction.atomic
def signal_set_active_from(request, pk: int):
    signal = get_object_or_404(Signal, pk=pk)
    active_from_raw = (request.POST.get("active_from") or "").strip()

    new_date = parse_date(active_from_raw)
    if not new_date:
        messages.error(request, "Ongeldige datum.")
        return redirect("signals:detail", pk=signal.pk)

    old = signal.active_from.isoformat() if signal.active_from else None
    if signal.active_from != new_date:
        signal.active_from = new_date
        signal.save(update_fields=["active_from"])
        log_history(signal, request.user, "active_from_changed", {"active_from": [old, new_date.isoformat()]})
        messages.success(request, "Actief vanaf bijgewerkt.")

    return redirect("signals:detail", pk=signal.pk)


@staff_required
@require_POST
@transaction.atomic
def signal_set_assignee(request, pk: int):
    signal = get_object_or_404(Signal, pk=pk)
    assigned_to = (request.POST.get("assigned_to") or "").strip()

    old_assigned_to_id = signal.assigned_to_id

    if assigned_to == "":
        signal.assigned_to = None
    elif assigned_to.isdigit():
        user = get_object_or_404(User, pk=int(assigned_to), is_staff=True)
        signal.assigned_to = user
        signal.assigned_by = request.user
    else:
        messages.error(request, "Ongeldige gebruiker.")
        return redirect("signals:detail", pk=signal.pk)

    update_fields = ["assigned_to"]
    if signal.assigned_to_id:
        update_fields.append("assigned_by")

    signal.save(update_fields=update_fields)

    if old_assigned_to_id != signal.assigned_to_id:
        log_history(signal, request.user, "reassigned", {"assigned_to_id": [old_assigned_to_id, signal.assigned_to_id]})

        if signal.assigned_to:
            create_signal_notifications(signal, request.user)

        messages.success(request, "Toewijzing bijgewerkt.")

    return redirect("signals:detail", pk=signal.pk)


@staff_required
@require_POST
@transaction.atomic
def signal_toggle_archive(request, pk: int):
    signal = get_object_or_404(Signal, pk=pk)

    old = signal.is_archived
    signal.is_archived = not signal.is_archived
    signal.save(update_fields=["is_archived"])

    log_history(signal, request.user, "archived_toggled", {"is_archived": [old, signal.is_archived]})
    messages.success(request, "Archiefstatus bijgewerkt.")

    return redirect("signals:list")


@staff_required
@require_POST
@transaction.atomic
def signal_toggle_archive_detail(request, pk: int):
    signal = get_object_or_404(Signal, pk=pk)

    old = signal.is_archived
    signal.is_archived = not signal.is_archived
    signal.save(update_fields=["is_archived"])

    log_history(signal, request.user, "archived_toggled", {"is_archived": [old, signal.is_archived]})
    messages.success(request, "Archiefstatus bijgewerkt.")

    return redirect("signals:detail", pk=signal.pk)


@login_required
def my_signals(request):
    signal_q = (request.GET.get("q") or "").strip()
    status_id = (request.GET.get("status") or "").strip()
    type_id = (request.GET.get("type") or "").strip()
    person_id = (request.GET.get("person") or "").strip()

    signals = (
        Signal.objects
        .select_related("type", "status", "assigned_to", "assigned_by")
        .prefetch_related("people")
        .filter(assigned_to=request.user)
    )

    if status_id.isdigit():
        signals = signals.filter(status_id=int(status_id))

    if type_id.isdigit():
        signals = signals.filter(type_id=int(type_id))

    if person_id.isdigit():
        signals = signals.filter(people__id=int(person_id)).distinct()

    if signal_q:
        signals = signals.filter(
            Q(name__icontains=signal_q)
            | Q(body__icontains=signal_q)
            | Q(type__name__icontains=signal_q)
            | Q(status__name__icontains=signal_q)
        )

    signals = signals.order_by("-active_from", "-created_at", "-id").distinct()

    statuses = Status.objects.filter(scope="signal", is_active=True).order_by("sort_order", "name")
    types = SignalType.objects.filter(is_active=True).order_by("sort_order", "name")
    people = Person.objects.order_by("last_name", "first_name")


    return render(request, "core/signals/my_list.html", {
        "signals": signals,
        "statuses": statuses,
        "types": types,
        "people": people,
        "signal_q": signal_q,
        "status_id": status_id,
        "type_id": type_id,
        "person_id": person_id,
        "active_nav": "my_signals",
    })