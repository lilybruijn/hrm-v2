from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from core.auth import staff_required
from core.models import WageValuePeriod, Person
from core.wage_values.forms import WageValuePeriodForm


@staff_required
def wage_value_list(request):
    archived = (request.GET.get("archived") or "").strip()

    periods = WageValuePeriod.objects.select_related(
        "person",
        "organization",
        "status",
        "decision_status",
    )

    if archived == "1":
        periods = periods.filter(is_archived=True)
    elif archived == "0":
        periods = periods.filter(is_archived=False)

    periods = periods.order_by("-start_date", "-id")

    return render(request, "core/wage_values/list.html", {
        "periods": periods,
        "archived": archived,
        "active_nav": "wage_values",
    })


@staff_required
def wage_value_create(request):
    person_id = request.GET.get("person")
    person = None

    if person_id:
        person = get_object_or_404(Person, pk=person_id, person_type="employee")

    if request.method == "POST":
        form = WageValuePeriodForm(request.POST, person=person)
        if form.is_valid():
            period = form.save()
            messages.success(request, "Loonwaardeperiode aangemaakt.")
            return redirect("wage_values:detail", pk=period.pk)
    else:
        form = WageValuePeriodForm(person=person)

    return render(request, "core/wage_values/form.html", {
        "form": form,
        "mode": "create",
        "active_nav": "wage_values",
    })


@staff_required
def wage_value_detail(request, pk: int):
    period = get_object_or_404(
        WageValuePeriod.objects.select_related("person", "organization", "status", "decision_status"),
        pk=pk
    )

    return render(request, "core/wage_values/detail.html", {
        "period": period,
        "active_nav": "wage_values",
    })


@staff_required
def wage_value_update(request, pk: int):
    period = get_object_or_404(WageValuePeriod, pk=pk)

    if request.method == "POST":
        form = WageValuePeriodForm(request.POST, instance=period)
        if form.is_valid():
            form.save()
            messages.success(request, "Loonwaardeperiode bijgewerkt.")
            return redirect("wage_values:detail", pk=period.pk)
    else:
        form = WageValuePeriodForm(instance=period)

    return render(request, "core/wage_values/form.html", {
        "form": form,
        "mode": "update",
        "period": period,
        "active_nav": "wage_values",
    })


@staff_required
@require_POST
def wage_value_archive(request, pk: int):
    period = get_object_or_404(WageValuePeriod, pk=pk)
    period.is_archived = True
    period.save(update_fields=["is_archived"])
    messages.success(request, "Loonwaardeperiode gearchiveerd.")
    return redirect("wage_values:list")


@staff_required
@require_POST
def wage_value_restore(request, pk: int):
    period = get_object_or_404(WageValuePeriod, pk=pk)
    period.is_archived = False
    period.save(update_fields=["is_archived"])
    messages.success(request, "Loonwaardeperiode hersteld.")
    return redirect("wage_values:list")