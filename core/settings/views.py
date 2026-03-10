from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.text import slugify

from core.auth import staff_required
from core.models.core import Signal, Task
from core.models.status import Status
from core.models.types import SignalType, TaskType
from core.settings.forms import SignalTypeForm, TaskTypeForm, StatusForm

def build_unique_status_key(name: str, scope: str, exclude_pk: int | None = None) -> str:
    base = slugify(name).replace("-", "_") or "status"
    key = base
    counter = 2

    qs = Status.objects.filter(scope=scope)
    if exclude_pk:
        qs = qs.exclude(pk=exclude_pk)

    while qs.filter(key=key).exists():
        key = f"{base}_{counter}"
        counter += 1

    return key

@staff_required
def settings_index(request):
    return render(request, "core/settings/index.html", {
        "active_nav": "settings",
    })


# =========================
# SIGNAL TYPES
# =========================


@staff_required
def signal_type_list(request):
    archived = (request.GET.get("archived") or "").strip()

    items = SignalType.objects.all()

    if archived == "1":
        items = items.filter(is_active=False)
    elif archived == "0":
        items = items.filter(is_active=True)

    items = items.order_by("sort_order", "name")

    return render(request, "core/settings/signal_types/list.html", {
        "items": items,
        "archived": archived,
        "active_nav": "settings",
    })


@staff_required
@transaction.atomic
def signal_type_create(request):
    if request.method == "POST":
        form = SignalTypeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Melding type toegevoegd.")
            return redirect("settings:signal_type_list")
    else:
        form = SignalTypeForm()

    return render(request, "core/settings/signal_types/form.html", {
        "form": form,
        "mode": "create",
        "active_nav": "settings",
    })


@staff_required
@transaction.atomic
def signal_type_update(request, pk: int):
    item = get_object_or_404(SignalType, pk=pk)

    if request.method == "POST":
        form = SignalTypeForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, "Melding type bijgewerkt.")
            return redirect("settings:signal_type_list")
    else:
        form = SignalTypeForm(instance=item)

    return render(request, "core/settings/signal_types/form.html", {
        "form": form,
        "item": item,
        "mode": "update",
        "active_nav": "settings",
    })


@staff_required
@transaction.atomic
def signal_type_archive(request, pk: int):
    item = get_object_or_404(SignalType, pk=pk)

    if request.method == "POST":
        item.is_active = False
        item.save(update_fields=["is_active"])
        messages.success(request, "Melding type gearchiveerd.")

    return redirect("settings:signal_type_list")


@staff_required
@transaction.atomic
def signal_type_restore(request, pk: int):
    item = get_object_or_404(SignalType, pk=pk)

    if request.method == "POST":
        item.is_active = True
        item.save(update_fields=["is_active"])
        messages.success(request, "Melding type hersteld.")

    return redirect("settings:signal_type_list")


@staff_required
@transaction.atomic
def signal_type_delete(request, pk: int):
    item = get_object_or_404(SignalType, pk=pk)

    if request.method != "POST":
        return redirect("settings:signal_type_list")

    if item.is_active:
        messages.error(request, "Archiveer dit melding type eerst voordat je het permanent verwijdert.")
        return redirect("settings:signal_type_list")

    in_use = Signal.objects.filter(type=item).exists()
    if in_use:
        messages.error(request, "Dit melding type is nog in gebruik en kan niet permanent worden verwijderd.")
        return redirect("settings:signal_type_list")

    item.delete()
    messages.success(request, "Melding type permanent verwijderd.")
    return redirect("settings:signal_type_list")


# =========================
# SIGNAL STATUSES
# =========================

@staff_required
@transaction.atomic
def signal_status_create(request):
    if request.method == "POST":
        form = StatusForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.scope = "signal"
            item.key = build_unique_status_key(item.name, "signal")
            item.save()
            messages.success(request, "Melding status toegevoegd.")
            return redirect("settings:signal_status_list")
    else:
        form = StatusForm()

    return render(request, "core/settings/signal_statuses/form.html", {
        "form": form,
        "mode": "create",
        "page_title": "Melding status toevoegen",
        "active_nav": "settings",
    })


@staff_required
@transaction.atomic
def signal_status_update(request, pk: int):
    item = get_object_or_404(Status, pk=pk, scope="signal")

    if request.method == "POST":
        old_name = item.name
        form = StatusForm(request.POST, instance=item)
        if form.is_valid():
            item = form.save(commit=False)
            item.scope = "signal"

            if item.name != old_name or not item.key:
                item.key = build_unique_status_key(item.name, "signal", exclude_pk=item.pk)

            item.save()
            messages.success(request, "Melding status bijgewerkt.")
            return redirect("settings:signal_status_list")
    else:
        form = StatusForm(instance=item)

    return render(request, "core/settings/signal_statuses/form.html", {
        "form": form,
        "item": item,
        "mode": "update",
        "page_title": "Melding status bewerken",
        "active_nav": "settings",
    })

@staff_required
def signal_status_list(request):
    archived = (request.GET.get("archived") or "").strip()

    items = Status.objects.filter(scope="signal")

    if archived == "1":
        items = items.filter(is_active=False)
    elif archived == "0":
        items = items.filter(is_active=True)

    items = items.order_by("sort_order", "name")

    return render(request, "core/settings/signal_statuses/list.html", {
        "items": items,
        "archived": archived,
        "active_nav": "settings",
    })


@staff_required
@transaction.atomic
def signal_status_archive(request, pk: int):
    item = get_object_or_404(Status, pk=pk, scope="signal")

    if request.method == "POST":
        item.is_active = False
        item.save(update_fields=["is_active"])
        messages.success(request, "Signal status gearchiveerd.")

    return redirect("settings:signal_status_list")


@staff_required
@transaction.atomic
def signal_status_restore(request, pk: int):
    item = get_object_or_404(Status, pk=pk, scope="signal")

    if request.method == "POST":
        item.is_active = True
        item.save(update_fields=["is_active"])
        messages.success(request, "Signal status hersteld.")

    return redirect("settings:signal_status_list")


@staff_required
@transaction.atomic
def signal_status_delete(request, pk: int):
    item = get_object_or_404(Status, pk=pk, scope="signal")

    if request.method != "POST":
        return redirect("settings:signal_status_list")

    in_use = Signal.objects.filter(status=item).exists()

    if in_use:
        messages.error(
            request,
            "Deze signal status is nog in gebruik en kan niet permanent worden verwijderd."
        )
        return redirect("settings:signal_status_list")

    item.delete()
    messages.success(request, "Signal status permanent verwijderd.")
    return redirect("settings:signal_status_list")
# =========================
# TASK TYPES
# =========================
@staff_required
def task_type_list(request):
    archived = (request.GET.get("archived") or "").strip()

    items = TaskType.objects.all()

    if archived == "1":
        items = items.filter(is_active=False)
    elif archived == "0":
        items = items.filter(is_active=True)

    items = items.order_by("sort_order", "name")

    return render(request, "core/settings/task_types/list.html", {
        "items": items,
        "archived": archived,
        "active_nav": "settings",
    })


@staff_required
@transaction.atomic
def task_type_create(request):
    if request.method == "POST":
        form = TaskTypeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Task type toegevoegd.")
            return redirect("settings:task_type_list")
    else:
        form = TaskTypeForm()

    return render(request, "core/settings/task_types/form.html", {
        "form": form,
        "mode": "create",
        "active_nav": "settings",
    })


@staff_required
@transaction.atomic
def task_type_update(request, pk: int):
    item = get_object_or_404(TaskType, pk=pk)

    if request.method == "POST":
        form = TaskTypeForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, "Task type bijgewerkt.")
            return redirect("settings:task_type_list")
    else:
        form = TaskTypeForm(instance=item)

    return render(request, "core/settings/task_types/form.html", {
        "form": form,
        "item": item,
        "mode": "update",
        "active_nav": "settings",
    })


@staff_required
@transaction.atomic
def task_type_archive(request, pk: int):
    item = get_object_or_404(TaskType, pk=pk)

    if request.method == "POST":
        item.is_active = False
        item.save(update_fields=["is_active"])
        messages.success(request, "Task type gearchiveerd.")

    return redirect("settings:task_type_list")


@staff_required
@transaction.atomic
def task_type_restore(request, pk: int):
    item = get_object_or_404(TaskType, pk=pk)

    if request.method == "POST":
        item.is_active = True
        item.save(update_fields=["is_active"])
        messages.success(request, "Task type hersteld.")

    return redirect("settings:task_type_list")


@staff_required
@transaction.atomic
def task_type_delete(request, pk: int):
    item = get_object_or_404(TaskType, pk=pk)

    if request.method != "POST":
        return redirect("settings:task_type_list")

    if item.is_active:
        messages.error(request, "Archiveer dit task type eerst voordat je het permanent verwijdert.")
        return redirect("settings:task_type_list")

    in_use = Task.objects.filter(type=item).exists()
    if in_use:
        messages.error(request, "Dit task type is nog in gebruik en kan niet permanent worden verwijderd.")
        return redirect("settings:task_type_list")

    item.delete()
    messages.success(request, "Task type permanent verwijderd.")
    return redirect("settings:task_type_list")

@staff_required
def task_status_list(request):
    archived = (request.GET.get("archived") or "").strip()

    items = Status.objects.filter(scope="task")

    if archived == "1":
        items = items.filter(is_active=False)
    elif archived == "0":
        items = items.filter(is_active=True)

    items = items.order_by("sort_order", "name")

    return render(request, "core/settings/task_statuses/list.html", {
        "items": items,
        "archived": archived,
        "active_nav": "settings",
    })


@staff_required
@transaction.atomic
def task_status_create(request):
    if request.method == "POST":
        form = StatusForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.scope = "task"
            item.save()
            messages.success(request, "Task status toegevoegd.")
            return redirect("settings:task_status_list")
    else:
        form = StatusForm()

    return render(request, "core/settings/task_statuses/form.html", {
        "form": form,
        "mode": "create",
        "active_nav": "settings",
    })


@staff_required
@transaction.atomic
def task_status_update(request, pk: int):
    item = get_object_or_404(Status, pk=pk, scope="task")

    if request.method == "POST":
        form = StatusForm(request.POST, instance=item)
        if form.is_valid():
            item = form.save(commit=False)
            item.scope = "task"
            item.save()
            messages.success(request, "Task status bijgewerkt.")
            return redirect("settings:task_status_list")
    else:
        form = StatusForm(instance=item)

    return render(request, "core/settings/task_statuses/form.html", {
        "form": form,
        "item": item,
        "mode": "update",
        "active_nav": "settings",
    })


@staff_required
@transaction.atomic
def task_status_archive(request, pk: int):
    item = get_object_or_404(Status, pk=pk, scope="task")

    if request.method == "POST":
        item.is_active = False
        item.save(update_fields=["is_active"])
        messages.success(request, "Task status gearchiveerd.")

    return redirect("settings:task_status_list")


@staff_required
@transaction.atomic
def task_status_restore(request, pk: int):
    item = get_object_or_404(Status, pk=pk, scope="task")

    if request.method == "POST":
        item.is_active = True
        item.save(update_fields=["is_active"])
        messages.success(request, "Task status hersteld.")

    return redirect("settings:task_status_list")


@staff_required
@transaction.atomic
def task_status_delete(request, pk: int):
    item = get_object_or_404(Status, pk=pk, scope="task")

    if request.method != "POST":
        return redirect("settings:task_status_list")

    if item.is_active:
        messages.error(request, "Archiveer deze task status eerst voordat je hem permanent verwijdert.")
        return redirect("settings:task_status_list")

    in_use = Task.objects.filter(status=item).exists()
    if in_use:
        messages.error(request, "Deze task status is nog in gebruik en kan niet permanent worden verwijderd.")
        return redirect("settings:task_status_list")

    item.delete()
    messages.success(request, "Task status permanent verwijderd.")
    return redirect("settings:task_status_list")