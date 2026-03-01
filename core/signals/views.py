from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.utils.dateparse import parse_date

from core.auth import staff_required
from core.models.notes import Note
from core.models.status import Status
from core.models.types import SignalType
from core.models.core import Signal
from .forms import SignalForm, NoteForm
from .services import log_history, create_signal_notifications

User = get_user_model()

@staff_required
def signal_list(request):
    qs = Signal.objects.select_related("type", "status", "assigned_to")

    # filters
    q = (request.GET.get("q") or "").strip()
    status_id = (request.GET.get("status") or "").strip()
    type_id = (request.GET.get("type") or "").strip()
    assignee_id = (request.GET.get("assignee") or "").strip()
    show_archived = request.GET.get("archived") == "1"

    if not show_archived:
        qs = qs.filter(is_archived=False)

    if assignee_id == "unassigned":
        qs = qs.filter(assigned_to__isnull=True)
    elif assignee_id.isdigit():
        qs = qs.filter(assigned_to_id=int(assignee_id))

    if status_id.isdigit():
        qs = qs.filter(status_id=int(status_id))
    if type_id.isdigit():
        qs = qs.filter(type_id=int(type_id))

    if q:
        qs = qs.filter(
            Q(body__icontains=q) |
            Q(assigned_to__username__icontains=q)
        )

    SORT_MAP = {
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

    qs = qs.order_by(f"{prefix}{sort_field}", "-active_from", "-created_at")

    paginator = Paginator(qs, 25)
    page_obj = paginator.get_page(request.GET.get("page"))

    statuses = Status.objects.filter(is_active=True).order_by("sort_order", "name")
    types = SignalType.objects.filter(is_active=True).order_by("sort_order", "name")

    assignees = User.objects.filter(is_staff=True, is_active=True).order_by("username")


    return render(request, "core/signals/list.html", {
        "page_obj": page_obj,
        "signals": page_obj.object_list,
        "q": q,
        "status_id": status_id,
        "type_id": type_id,
        "assignee_id": assignee_id,
        "assignees": assignees,
        "show_archived": show_archived,
        "statuses": statuses,
        "types": types,
        "sort": sort,  
        "dir": dir_,   
        "active_nav": "signals",
    })


@staff_required
@transaction.atomic
def signal_create(request):
    if request.method == "POST":
        form = SignalForm(request.POST)
        if form.is_valid():
            signal = form.save()
            log_history(signal, request.user, "created", {})
            create_signal_notifications(signal, request.user)
            messages.success(request, "Melding aangemaakt.")
            return redirect("signals:detail", pk=signal.id)
    else:
        initial = { "active_from": timezone.now() }
        form = SignalForm(initial=initial)

    return render(request, "core/signals/form.html", {
        "form": form,
        "mode": "create",
        "active_nav": "signals",
    })


@staff_required
def signal_detail(request, pk: int):
    signal = get_object_or_404(
        Signal.objects.select_related("type", "status", "assigned_to"),
        pk=pk
    )

    form = SignalForm(instance=signal)
    note_form = NoteForm()

    statuses = Status.objects.filter(is_active=True).order_by("sort_order", "name")
    types = SignalType.objects.filter(is_active=True).order_by("sort_order", "name")
    assignees = User.objects.filter(is_staff=True, is_active=True).order_by("username")

    notes = signal.notes.select_related("author").all()
    history = signal.history.select_related("actor").all()

    status_map = {s.id: s.name for s in Status.objects.all()}
    type_map = {t.id: t.name for t in SignalType.objects.all()}
    user_map = {u.id: u.username for u in User.objects.all()}

    ACTION_LABELS = {
        "created": "Melding aangemaakt",
        "updated": "Melding bijgewerkt",
        "status_changed": "Status gewijzigd",
        "type_changed": "Type gewijzigd",
        "active_from_changed": "Actief vanaf aangepast",
        "reassigned": "Toewijzing gewijzigd",
        "archived_toggled": "Archiefstatus gewijzigd",
        "note_added": "Notitie toegevoegd",
    }

    for h in history:
        h.action_label = ACTION_LABELS.get(h.action, h.action.replace("_", " ").capitalize())

    return render(request, "core/signals/detail.html", {
        "signal": signal,
        "form": form,
        "note_form": note_form,
        "statuses": statuses,
        "types": types,
        "assignees": assignees,
        "notes": notes,
        "history": history,
        "active_nav": "signals",
        "status_map": status_map,
        "type_map": type_map,
        "user_map": user_map,
    })


@staff_required
@transaction.atomic
def signal_update(request, pk: int):
    signal = get_object_or_404(Signal.objects.select_related("type", "status", "assigned_to"), pk=pk)

    if request.method != "POST":
        return redirect("signals:detail", pk=signal.pk)

    before = {
        "type_id": signal.type_id,
        "assigned_to_id": signal.assigned_to_id,
        "status_id": signal.status_id,
        "active_from": signal.active_from.isoformat() if signal.active_from else None,
        "body": signal.body,
        "is_archived": signal.is_archived,
    }

    data = request.POST.copy()

    # velden die je form verwacht
    expected_fields = ["type", "active_from", "status", "assigned_to", "body"]

    for f in expected_fields:
        if f not in data or data.get(f) in (None, ""):
            if f in ("type", "status", "assigned_to"):
                data[f] = str(getattr(signal, f"{f}_id") or "")
            elif f == "active_from":
                data[f] = signal.active_from.isoformat() if signal.active_from else ""
            else:  # body
                data[f] = getattr(signal, f) or ""

    form = SignalForm(data, instance=signal)
    if not form.is_valid():
        messages.error(request, "Formulier is niet geldig.")

        # opnieuw alles laden wat je detail template verwacht
        note_form = NoteForm()
        statuses = Status.objects.filter(is_active=True).order_by("sort_order", "name")
        types = SignalType.objects.filter(is_active=True).order_by("sort_order", "name")
        assignees = User.objects.filter(is_staff=True, is_active=True).order_by("username")
        notes = signal.notes.select_related("author").all()
        history = signal.history.select_related("actor").all()

        return render(request, "core/signals/detail.html", {
            "signal": signal,
            "form": form,  # ✅ met errors
            "note_form": note_form,
            "statuses": statuses,
            "types": types,
            "assignees": assignees,
            "notes": notes,
            "history": history,
            "active_nav": "signals",
        })

    signal = form.save()

    after = {
        "type_id": signal.type_id,
        "assigned_to_id": signal.assigned_to_id,
        "status_id": signal.status_id,
        "active_from": signal.active_from.isoformat() if signal.active_from else None,
        "body": signal.body,
        "is_archived": signal.is_archived,
    }

    changes = {k: [before[k], after[k]] for k in before if before[k] != after[k]}

    if changes:
        log_history(signal, request.user, "updated", changes)
        messages.success(request, "Melding bijgewerkt.")

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

    new_date = parse_date(active_from_raw)  # verwacht YYYY-MM-DD
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

    old = signal.assigned_to_id

    if assigned_to == "":
        signal.assigned_to = None
    elif assigned_to.isdigit():
        user = get_object_or_404(User, pk=int(assigned_to), is_staff=True)
        signal.assigned_to = user
    else:
        messages.error(request, "Ongeldige gebruiker.")
        return redirect("signals:detail", pk=signal.pk)

    signal.save(update_fields=["assigned_to"])
    if old != signal.assigned_to_id:
        log_history(signal, request.user, "reassigned", {"assigned_to_id": [old, signal.assigned_to_id]})
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
    return redirect("signals:detail", pk=signal.pk)