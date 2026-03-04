from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from core.auth import staff_required
from core.models import Task, Note, Status, TaskType
from .forms import TaskForm
from core.signals.services import log_history

User = get_user_model()


@staff_required
def task_list(request):
    qs = Task.objects.select_related("type", "status", "assigned_to")

    # filters
    q = (request.GET.get("q") or "").strip()
    status_id = (request.GET.get("status") or "").strip()
    type_id = (request.GET.get("type") or "").strip()
    assignee_id = (request.GET.get("assignee") or "").strip()
    show_archived = request.GET.get("archived") == "1"

    if not show_archived:
        qs = qs.filter(is_archived=False)

    if assignee_id.isdigit():
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
    qs = qs.order_by(f"{prefix}{sort_field}", "id")

    paginator = Paginator(qs, 25)
    page_obj = paginator.get_page(request.GET.get("page"))

    statuses = Status.objects.filter(scope="task", is_active=True).order_by("sort_order", "name")
    types = TaskType.objects.filter(is_active=True).order_by("sort_order", "name")

    # assignees: alle users die minimaal 1 task hebben
    assignees = (
        User.objects
        .filter(tasks__isnull=False)
        .distinct()
        .order_by("username")
    )

    return render(request, "core/tasks/list.html", {
        "page_obj": page_obj,
        "tasks": page_obj.object_list,
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
        "active_nav": "tasks",
    })


@staff_required
@transaction.atomic
def task_create(request):
    if request.method == "POST":
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save()
            log_history(task, request.user, "created", {})
            messages.success(request, "Task aangemaakt.")
            return redirect("tasks:detail", pk=task.pk)
    else:
        form = TaskForm()

    return render(request, "core/tasks/form.html", {
        "form": form,
        "mode": "create",
        "active_nav": "tasks",
    })


@staff_required
def task_detail(request, pk: int):
    task = get_object_or_404(Task.objects.select_related("type", "status", "assigned_to"), pk=pk)
    form = TaskForm(instance=task)

    notes = task.notes.select_related("author").all().order_by("-created_at")
    history = task.history.select_related("actor").all().order_by("-created_at")

    ACTION_LABELS = {
        "created": "Task aangemaakt",
        "updated": "Task bijgewerkt",
        "archived_toggled": "Archiefstatus gewijzigd",
        "note_added": "Notitie toegevoegd",
    }
    for h in history:
        h.action_label = ACTION_LABELS.get(h.action, h.action.replace("_", " ").capitalize())

    return render(request, "core/tasks/detail.html", {
        "task": task,
        "form": form,
        "notes": notes,
        "history": history,
        "active_nav": "tasks",
    })


@staff_required
@transaction.atomic
def task_update(request, pk: int):
    task = get_object_or_404(Task.objects.select_related("type", "status", "assigned_to"), pk=pk)

    if request.method != "POST":
        return redirect("tasks:detail", pk=task.pk)

    before = {
        "type_id": task.type_id,
        "assigned_to_id": task.assigned_to_id,
        "status_id": task.status_id,
        "due_at": task.due_at.isoformat() if task.due_at else None,
        "body": task.body,
        "is_archived": task.is_archived,
    }

    form = TaskForm(request.POST, instance=task)
    if not form.is_valid():
        messages.error(request, "Formulier is niet geldig.")
        return redirect("tasks:detail", pk=task.pk)

    task = form.save()

    after = {
        "type_id": task.type_id,
        "assigned_to_id": task.assigned_to_id,
        "status_id": task.status_id,
        "due_at": task.due_at.isoformat() if task.due_at else None,
        "body": task.body,
        "is_archived": task.is_archived,
    }

    changes = {k: [before[k], after[k]] for k in before if before[k] != after[k]}
    if changes:
        log_history(task, request.user, "updated", changes)
        messages.success(request, "Task bijgewerkt.")

    return redirect("tasks:detail", pk=task.pk)


@staff_required
@require_POST
@transaction.atomic
def task_add_note(request, pk: int):
    task = get_object_or_404(Task, pk=pk)
    body = (request.POST.get("body") or "").strip()

    if not body:
        messages.error(request, "Notitie is leeg.")
        return redirect("tasks:detail", pk=task.pk)

    note: Note = Note.objects.create(author=request.user, body=body, content_object=task)
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
    return redirect("tasks:detail", pk=task.pk)