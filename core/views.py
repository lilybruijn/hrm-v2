from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import render

from core.auth import staff_required
from core.models.core import Signal, Task
from core.models.people import Person


class AppLoginView(LoginView):
    template_name = "core/auth/login.html"


class AppLogoutView(LogoutView):
    pass


@staff_required
def dashboard(request):
    signals_open_count = Signal.objects.filter(is_archived=False).count()
    tasks_open_count = Task.objects.filter(is_archived=False).count()
    people_active_count = Person.objects.filter(is_archived=False).count()

    return render(request, "core/dashboard.html", {
        "signals_open_count": signals_open_count,
        "tasks_open_count": tasks_open_count,
        "people_active_count": people_active_count,
    })