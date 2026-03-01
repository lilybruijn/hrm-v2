from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import render
from django.contrib.contenttypes.models import ContentType

from core.models.history import HistoryEvent
from core.models.notifications import Notification
from core.models.core import Signal

class AppLoginView(LoginView):
    template_name = "core/auth/login.html"


class AppLogoutView(LogoutView):
    pass
@login_required
def dashboard(request):
    notification_ct = ContentType.objects.get_for_model(Notification)

    activity_qs = (
        HistoryEvent.objects
        .select_related("actor", "content_type")
        .exclude(content_type=notification_ct)
        .order_by("-created_at")[:10]
    )

    ACTION_LABELS = {
        "created": "Aangemaakt",
        "updated": "Bijgewerkt",
        "deleted": "Verwijderd",
        "status_changed": "Status gewijzigd",
        "type_changed": "Type gewijzigd",
        "active_from_changed": "Actief vanaf aangepast",
        "reassigned": "Toewijzing gewijzigd",
        "archived_toggled": "Archiefstatus gewijzigd",
        "note_added": "Notitie toegevoegd",
    }

    ACTION_COLORS = {
        "created": "bg-success",
        "updated": "bg-primary",
        "deleted": "bg-danger",
        "status_changed": "bg-info",
        "type_changed": "bg-info",
        "active_from_changed": "bg-secondary",
        "reassigned": "bg-warning",
        "archived_toggled": "bg-dark",
        "note_added": "bg-warning", 
    }

    activities = []
    for h in activity_qs:
        action_label = ACTION_LABELS.get(h.action, h.action.replace("_", " ").capitalize())
        actor_label = h.actor.username if h.actor_id else "Systeem"

        model = h.content_type.model if h.content_type_id else None
        obj_id = h.object_id

        url = None
        if model == "signal" and obj_id:
            url = f"/signals/{obj_id}/"

        color_class = ACTION_COLORS.get(h.action, "bg-secondary")

        activities.append({
            "title": action_label,
            "subtitle": f"{actor_label} · {h.content_type.name if h.content_type_id else 'Onbekend'} #{obj_id}",
            "time": h.created_at,
            "url": url,
            "color": color_class,
        })

    return render(request, "core/dashboard.html", {
        "active_nav": "dashboard",
        "activities": activities,
    })