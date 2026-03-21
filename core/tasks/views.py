from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from datetime import timedelta
from django.utils import timezone
from core.auth import staff_required
from core.models import Task, Note, Status, TaskType, Signal
from core.models.people import Person
from core.signals.services import log_history
from .forms import TaskForm, TaskCreateForm
from .services import create_task_notifications, create_admin_review_task_for_completed_task
User = get_user_model()

ACTION_LABELS = {
    "created": "Taak aangemaakt",
    "updated": "Taak bijgewerkt",
    "status_changed": "Status gewijzigd",
    "type_changed": "Type gewijzigd",
    "reassigned": "Toewijzing gewijzigd",
    "archived_toggled": "Archiefstatus gewijzigd",
    "note_added": "Notitie toegevoegd",
}


@staff_required
def task_list(request):
    qs = (
        Task.objects
        .select_related("type", "status", "assigned_to", "assigned_by", "signal")
        .prefetch_related("people")
    )

    task_q = (request.GET.get("task_q") or "").strip()
    status_id = (request.GET.get("task_status") or "").strip()
    type_id = (request.GET.get("task_type") or "").strip()
    assignee_id = (request.GET.get("task_assignee") or "").strip()
    person_id = (request.GET.get("task_person") or "").strip()
    signal_id = (request.GET.get("task_signal") or "").strip()
    archived = (request.GET.get("archived") or "").strip()

    if archived == "1":
        qs = qs.filter(is_archived=True)
    elif archived == "0":
        qs = qs.filter(is_archived=False)

    if assignee_id.isdigit():
        qs = qs.filter(assigned_to_id=int(assignee_id))

    if status_id.isdigit():
        qs = qs.filter(status_id=int(status_id))

    if type_id.isdigit():
        qs = qs.filter(type_id=int(type_id))

    if person_id.isdigit():
        qs = qs.filter(people__id=int(person_id)).distinct()

    if signal_id.isdigit():
        qs = qs.filter(signal_id=int(signal_id))

    if task_q:
        qs = qs.filter(
            Q(body__icontains=task_q) |
            Q(assigned_to__username__icontains=task_q)
        )

    SORT_MAP = {
        "id": "id",
        "due_at": "due_at",
        "type": "type__name",
        "status": "status__name",
        "assigned_to": "assigned_to__username",
        "created_at": "created_at",
    }

    sort = (request.GET.get("sort") or "due_at").strip()
    dir_ = (request.GET.get("dir") or "asc").strip().lower()

    if dir_ not in ("asc", "desc"):
        dir_ = "asc"

    sort_field = SORT_MAP.get(sort, "due_at")
    prefix = "-" if dir_ == "desc" else ""
    qs = qs.order_by(f"{prefix}{sort_field}", "id").distinct()

    paginator = Paginator(qs, 25)
    page_obj = paginator.get_page(request.GET.get("page"))

    statuses = Status.objects.filter(scope="task", is_active=True).order_by("sort_order", "name")
    types = TaskType.objects.filter(is_active=True).order_by("sort_order", "name")
    people = Person.objects.order_by("last_name", "first_name")
    signals = Signal.objects.filter(is_archived=False).order_by("-id")

    assignees = (
        User.objects
        .filter(tasks__isnull=False, is_staff=True, is_active=True)
        .distinct()
        .order_by("username")
    )

    return render(request, "core/tasks/list.html", {
        "page_obj": page_obj,
        "tasks": page_obj.object_list,
        "task_q": task_q,
        "person_id": person_id,
        "signal_id": signal_id,
        "status_id": status_id,
        "type_id": type_id,
        "assignee_id": assignee_id,
        "assignees": assignees,
        "statuses": statuses,
        "types": types,
        "people": people,
        "signals": signals,
        "archived": archived,
        "sort": sort,
        "dir": dir_,
        "active_nav": "tasks",
    })


@staff_required
@transaction.atomic
def task_create(request):
    people_param = (request.GET.get("people") or "").strip()
    signal_id = (request.GET.get("signal") or "").strip()
    signal = None
    assigned_to_id = (request.GET.get("assigned_to") or "").strip()
    if signal_id.isdigit():
        signal = Signal.objects.prefetch_related("people").filter(pk=int(signal_id)).first()

    if request.method == "POST":
        form = TaskCreateForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)

            if task.assigned_to:
                task.assigned_by = request.user

            task.save()
            form.save_m2m()

            log_history(task, request.user, "created", {})

            if task.assigned_to:
                create_task_notifications(task, request.user)

            messages.success(request, "Taak aangemaakt.")
            return redirect("tasks:detail", pk=task.id)
    else:
        initial = {}
        if signal:
            initial["signal"] = signal.id
            initial["people"] = list(signal.people.values_list("id", flat=True))
        if people_param:
            ids = [int(x) for x in people_param.split(",") if x.strip().isdigit()]
            initial["people"] = ids
        if assigned_to_id.isdigit():
            initial["assigned_to"] = int(assigned_to_id)
        form = TaskCreateForm(initial=initial)

    return render(request, "core/tasks/form.html", {
        "form": form,
        "mode": "create",
        "active_nav": "tasks",
    })


@staff_required
def task_detail(request, pk: int):
    task = get_object_or_404(
        Task.objects.select_related(
            "type", "status", "assigned_to", "assigned_by", "signal", "parent_task"
        ).prefetch_related("people", "child_tasks"),
        pk=pk,
    )
    form = TaskForm(instance=task)

    notes = task.notes.select_related("author").order_by("-created_at")[:25]
    history = task.history.select_related("actor").order_by("-created_at")[:25]

    status_map = {s.id: s.name for s in Status.objects.filter(scope="task")}
    type_map = {t.id: t.name for t in TaskType.objects.all()}
    user_map = {u.id: u.username for u in User.objects.all()}
    person_map = {p.id: f"{p.first_name} {p.last_name}" for p in Person.objects.all()}
    signal_map = {s.id: f"Melding #{s.id} - {s.type.name}" for s in Signal.objects.select_related("type")}

    for h in history:
        h.action_label = ACTION_LABELS.get(h.action, h.action.replace("_", " ").capitalize())

    return render(request, "core/tasks/detail.html", {
        "task": task,
        "form": form,
        "notes": notes,
        "history": history,
        "active_nav": "tasks",
        "status_map": status_map,
        "type_map": type_map,
        "user_map": user_map,
        "person_map": person_map,
        "signal_map": signal_map,
    })


@staff_required
@transaction.atomic
def task_update(request, pk: int):
    task = get_object_or_404(
        Task.objects
        .select_related("type", "status", "assigned_to", "assigned_by", "signal")
        .prefetch_related("people"),
        pk=pk,
    )

    if request.method != "POST":
        return redirect("tasks:detail", pk=task.pk)

    old_assigned_to_id = task.assigned_to_id

    before = {
        "type_id": task.type_id,
        "assigned_to_id": task.assigned_to_id,
        "signal_id": task.signal_id,
        "status_id": task.status_id,
        "due_at": task.due_at.strftime("%Y-%m-%d") if task.due_at else "",
        "body": task.body,
        "is_archived": task.is_archived,
    }
    before_people = list(task.people.values_list("id", flat=True))

    data = request.POST.copy()
    expected_fields = ["type", "assigned_to", "signal", "due_at", "status", "body"]

    for f in expected_fields:
        if f not in data:
            if f in ("type", "assigned_to", "signal", "status"):
                data[f] = str(getattr(task, f"{f}_id") or "")
            elif f == "due_at":
                data[f] = task.due_at.strftime("%Y-%m-%d") if task.due_at else ""
            else:
                data[f] = task.body or ""

    form = TaskForm(data, instance=task)

    if not form.is_valid():
        messages.error(request, "Formulier is niet geldig.")

        notes = task.notes.select_related("author").all().order_by("-created_at")[:25]
        history = task.history.select_related("actor").all().order_by("-created_at")[:25]

        status_map = {s.id: s.name for s in Status.objects.filter(scope="task")}
        type_map = {t.id: t.name for t in TaskType.objects.all()}
        user_map = {u.id: u.username for u in User.objects.all()}
        person_map = {p.id: f"{p.first_name} {p.last_name}" for p in Person.objects.all()}
        signal_map = {s.id: f"Melding #{s.id} - {s.type.name}" for s in Signal.objects.select_related("type")}

        for h in history:
            h.action_label = ACTION_LABELS.get(h.action, h.action.replace("_", " ").capitalize())

        return render(request, "core/tasks/detail.html", {
            "task": task,
            "form": form,
            "notes": notes,
            "history": history,
            "active_nav": "tasks",
            "status_map": status_map,
            "type_map": type_map,
            "user_map": user_map,
            "person_map": person_map,
            "signal_map": signal_map,
        })

    task = form.save(commit=False)

    assignment_changed = task.assigned_to_id != old_assigned_to_id
    if assignment_changed and task.assigned_to:
        task.assigned_by = request.user

    task.save()
    form.save_m2m()
    after_people = list(task.people.values_list("id", flat=True))
    completed_status = Status.objects.filter(
        scope="task",
        name__iexact="Afgerond",
        is_active=True,
    ).first()

    if (
        completed_status
        and before["status_id"] != completed_status.id
        and task.status_id == completed_status.id
        and not task.parent_task_id
        and not task.child_tasks.exists()
    ):
        create_admin_review_task_for_completed_task(task, request.user)
    
    after = {
        "type_id": task.type_id,
        "assigned_to_id": task.assigned_to_id,
        "signal_id": task.signal_id,
        "status_id": task.status_id,
        "due_at": task.due_at.strftime("%Y-%m-%d") if task.due_at else "",
        "body": task.body,
        "is_archived": task.is_archived,
    }

    changes = {k: [before[k], after[k]] for k in before if before[k] != after[k]}
    
    if before_people != after_people:
        changes["people"] = [before_people, after_people]

    if changes:
        log_history(task, request.user, "updated", changes)

        if assignment_changed and task.assigned_to:
            create_task_notifications(task, request.user, reassigned=True)

        messages.success(request, "Taak bijgewerkt.")

    return redirect("tasks:detail", pk=task.pk)


@staff_required
@require_POST
@transaction.atomic
def task_update_body(request, pk: int):
    task = get_object_or_404(Task, pk=pk)

    new_body = (request.POST.get("body") or "").strip()
    old_body = task.body or ""

    if new_body != old_body:
        task.body = new_body
        task.save(update_fields=["body"])
        log_history(task, request.user, "updated", {"body": [old_body, new_body]})
        messages.success(request, "Omschrijving bijgewerkt.")

    return redirect("tasks:detail", pk=task.pk)


@staff_required
@require_POST
@transaction.atomic
def task_restore(request, pk: int):
    task = get_object_or_404(Task, pk=pk)

    if task.is_archived:
        task.is_archived = False
        task.save(update_fields=["is_archived"])
        messages.success(request, "Taak hersteld.")

    return redirect("tasks:list")


@staff_required
@require_POST
@transaction.atomic
def task_delete(request, pk: int):
    task = get_object_or_404(Task, pk=pk)

    if not task.is_archived:
        messages.error(request, "Archiveer de taak eerst voordat je deze permanent verwijdert.")
        return redirect("tasks:list")

    task.delete()
    messages.success(request, "Taak permanent verwijderd.")
    return redirect("tasks:list")


@staff_required
@require_POST
@transaction.atomic
def task_add_note(request, pk: int):
    task = get_object_or_404(Task, pk=pk)
    body = (request.POST.get("body") or "").strip()

    if not body:
        messages.error(request, "Notitie is leeg.")
        return redirect("tasks:detail", pk=task.pk)

    note = Note.objects.create(author=request.user, body=body, content_object=task)
    log_history(task, request.user, "note_added", {"note_id": [None, note.id]})
    messages.success(request, "Notitie toegevoegd.")
    return redirect("tasks:detail", pk=task.pk)


@staff_required
@require_POST
@transaction.atomic
def task_toggle_archive(request, pk: int):
    task = get_object_or_404(Task, pk=pk)
    old = task.is_archived
    task.is_archived = not task.is_archived
    task.save(update_fields=["is_archived"])
    log_history(task, request.user, "archived_toggled", {"is_archived": [old, task.is_archived]})
    messages.success(request, "Archiefstatus bijgewerkt.")
    return redirect("tasks:list")


@staff_required
@require_POST
@transaction.atomic
def task_toggle_archive_detail(request, pk: int):
    task = get_object_or_404(Task, pk=pk)
    old = task.is_archived
    task.is_archived = not task.is_archived
    task.save(update_fields=["is_archived"])
    log_history(task, request.user, "archived_toggled", {"is_archived": [old, task.is_archived]})
    messages.success(request, "Archiefstatus bijgewerkt.")
    return redirect("tasks:detail", pk=task.pk)

from datetime import timedelta
from django.utils import timezone
from django.db.models import Q

@login_required
def my_tasks(request):
    task_q = (request.GET.get("q") or "").strip()
    status_id = (request.GET.get("status") or "").strip()
    type_id = (request.GET.get("type") or "").strip()
    person_id = (request.GET.get("person") or "").strip()
    signal_id = (request.GET.get("signal") or "").strip()

    hide_completed = request.GET.get("hide_completed", "1") == "1"

    tasks = (
        Task.objects
        .select_related("type", "status", "assigned_to", "assigned_by", "signal")
        .prefetch_related("people")
        .filter(assigned_to=request.user)
    )

    if hide_completed:
        tasks = tasks.exclude(status__name__iexact="Afgerond")

    if status_id.isdigit():
        tasks = tasks.filter(status_id=int(status_id))

    if type_id.isdigit():
        tasks = tasks.filter(type_id=int(type_id))

    if person_id.isdigit():
        tasks = tasks.filter(people__id=int(person_id)).distinct()

    if signal_id.isdigit():
        tasks = tasks.filter(signal_id=int(signal_id))

    if task_q:
        tasks = tasks.filter(
            Q(body__icontains=task_q)
            | Q(type__name__icontains=task_q)
            | Q(status__name__icontains=task_q)
            | Q(signal__name__icontains=task_q)
        )

    tasks = list(tasks.distinct())

    today = timezone.localdate()
    soon_date = today + timedelta(days=3)

    for task in tasks:
        if task.due_at:
            if task.due_at < today:
                task.urgency = "overdue"
                task.urgency_rank = 0
            elif task.due_at == today:
                task.urgency = "today"
                task.urgency_rank = 1
            elif task.due_at <= soon_date:
                task.urgency = "soon"
                task.urgency_rank = 2
            else:
                task.urgency = "later"
                task.urgency_rank = 3
        else:
            task.urgency = "no_deadline"
            task.urgency_rank = 4

    tasks.sort(
        key=lambda task: (
            task.urgency_rank,
            task.due_at or today + timedelta(days=99999),
            -(task.id or 0),
        )
    )

    statuses = Status.objects.filter(scope="task", is_active=True).order_by("sort_order", "name")
    types = TaskType.objects.filter(is_active=True).order_by("sort_order", "name")
    people = Person.objects.order_by("last_name", "first_name")

    signals = (
        Signal.objects
        .filter(tasks__assigned_to=request.user)
        .distinct()
        .order_by("-id")
    )

    return render(request, "core/tasks/my_list.html", {
        "tasks": tasks,
        "statuses": statuses,
        "types": types,
        "people": people,
        "signals": signals,
        "task_q": task_q,
        "status_id": status_id,
        "type_id": type_id,
        "person_id": person_id,
        "signal_id": signal_id,
        "hide_completed": hide_completed,
        "active_nav": "my_tasks",
    })