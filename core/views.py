from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import render


class AppLoginView(LoginView):
    template_name = "core/auth/login.html"


class AppLogoutView(LogoutView):
    pass


@login_required
def dashboard(request):
    return render(request, "core/dashboard.html", {"active_nav": "dashboard"})