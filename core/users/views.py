from django.contrib import messages
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from core.auth import staff_required
from .forms import UserCreateForm, UserUpdateForm

User = get_user_model()


@staff_required
def user_list(request):
    users = User.objects.prefetch_related("groups").all().order_by("username")

    return render(request, "core/users/list.html", {
        "users": users,
        "active_nav": "users",
    })


@staff_required
def user_create(request):
    if request.method == "POST":
        form = UserCreateForm(request.POST)
        if form.is_valid():
            user = form.save()

            group = form.cleaned_data.get("group")
            user.groups.clear()
            if group:
                user.groups.add(group)

            messages.success(request, f"Gebruiker {user.username} aangemaakt.")
            return redirect("users:list")
    else:
        form = UserCreateForm(initial={
            "is_active": True,
        })

    return render(request, "core/users/form.html", {
        "form": form,
        "mode": "create",
        "active_nav": "users",
    })
@staff_required
def user_update(request, pk: int):
    user_obj = get_object_or_404(User, pk=pk)

    if request.method == "POST":
        form = UserUpdateForm(request.POST, instance=user_obj)
        if form.is_valid():
            user_obj = form.save()

            group = form.cleaned_data.get("group")
            user_obj.groups.clear()
            if group:
                user_obj.groups.add(group)

            messages.success(request, f"Gebruiker {user_obj.username} bijgewerkt.")
            return redirect("users:list")
    else:
        form = UserUpdateForm(instance=user_obj)

    return render(request, "core/users/form.html", {
        "form": form,
        "mode": "update",
        "user_obj": user_obj,
        "active_nav": "users",
    })
@staff_required
@require_POST
def user_toggle_active(request, pk: int):
    user_obj = get_object_or_404(User, pk=pk)

    if request.user.id == user_obj.id:
        messages.error(request, "Je kunt je eigen account niet deactiveren.")
        return redirect("users:list")

    user_obj.is_active = not user_obj.is_active
    user_obj.save(update_fields=["is_active"])

    if user_obj.is_active:
        messages.success(request, f"Gebruiker {user_obj.username} is geactiveerd.")
    else:
        messages.success(request, f"Gebruiker {user_obj.username} is gedeactiveerd.")

    return redirect("users:list")


