# core/views_users.py


from core.auth import staff_required
from django.contrib.auth import get_user_model
from django.shortcuts import render

User = get_user_model()

@staff_required
def list(request):
    if not request.user.is_staff:
        return HttpResponseForbidden()

    users = User.objects.all().order_by("username")

    return render(request, "core/users/list.html", {
        "users": users,        
        "active_nav": "users",
    })