from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from core.auth import staff_required
from core.models import JobCoachingPeriod, Person
from core.jobcoaching.forms import JobCoachingPeriodForm


@staff_required
def jobcoaching_list(request):
    archived = (request.GET.get("archived") or "").strip()

    periods = JobCoachingPeriod.objects.select_related(
        "person",
        "organization",
        "status",
    )

    if archived == "1":
        periods = periods.filter(is_archived=True)
    elif archived == "0":
        periods = periods.filter(is_archived=False)

    periods = periods.order_by("-start_date", "-id")

    return render(request, "core/jobcoaching/list.html", {
        "periods": periods,
        "archived": archived,
        "active_nav": "jobcoaching",
    })


@staff_required
def jobcoaching_create(request):
    person_id = request.GET.get("person")
    person = None

    if person_id:
        person = get_object_or_404(Person, pk=person_id, person_type="employee")

    if request.method == "POST":
        form = JobCoachingPeriodForm(request.POST, person=person)
        if form.is_valid():
            period = form.save()
            messages.success(request, "Jobcoachingperiode aangemaakt.")
            return redirect("jobcoaching:detail", pk=period.pk)
    else:
        form = JobCoachingPeriodForm(person=person)

    return render(request, "core/jobcoaching/form.html", {
        "form": form,
        "mode": "create",
        "active_nav": "jobcoaching",
    })


@staff_required
def jobcoaching_detail(request, pk: int):
    period = get_object_or_404(
        JobCoachingPeriod.objects.select_related("person", "organization", "status"),
        pk=pk
    )

    return render(request, "core/jobcoaching/detail.html", {
        "period": period,
        "active_nav": "jobcoaching",
    })


@staff_required
def jobcoaching_update(request, pk: int):
    period = get_object_or_404(JobCoachingPeriod, pk=pk)

    if request.method == "POST":
        form = JobCoachingPeriodForm(request.POST, instance=period)
        if form.is_valid():
            form.save()
            messages.success(request, "Jobcoachingperiode bijgewerkt.")
            return redirect("jobcoaching:detail", pk=period.pk)
    else:
        form = JobCoachingPeriodForm(instance=period)

    return render(request, "core/jobcoaching/form.html", {
        "form": form,
        "mode": "update",
        "period": period,
        "active_nav": "jobcoaching",
    })


@staff_required
@require_POST
def jobcoaching_archive(request, pk: int):
    period = get_object_or_404(JobCoachingPeriod, pk=pk)
    period.is_archived = True
    period.save(update_fields=["is_archived"])
    messages.success(request, "Jobcoachingperiode gearchiveerd.")
    return redirect("jobcoaching:list")


@staff_required
@require_POST
def jobcoaching_restore(request, pk: int):
    period = get_object_or_404(JobCoachingPeriod, pk=pk)
    period.is_archived = False
    period.save(update_fields=["is_archived"])
    messages.success(request, "Jobcoachingperiode hersteld.")
    return redirect("jobcoaching:list")