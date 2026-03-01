from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render

from core.auth import staff_required
from core.models.history import HistoryEvent
from core.models.notifications import Notification


@staff_required
def activities_list(request):
    qs = HistoryEvent.objects.select_related("actor", "content_type").order_by("-created_at")

    # exclude notifications
    notification_ct = ContentType.objects.get_for_model(Notification)
    qs = qs.exclude(content_type=notification_ct)

    # filters
    q = (request.GET.get("q") or "").strip()
    action = (request.GET.get("action") or "").strip()
    model = (request.GET.get("model") or "").strip()

    if q:
        qs = qs.filter(
            Q(actor__username__icontains=q)
            | Q(action__icontains=q)
            | Q(changes__icontains=q)
        )

    if action:
        qs = qs.filter(action=action)

    if model:
        qs = qs.filter(content_type__model=model)

    # dropdown opties
    raw_actions = (
        HistoryEvent.objects
        .exclude(content_type=notification_ct)
        .values_list("action", flat=True)
        .distinct()
        .order_by("action")
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

    actions = [
        {
            "value": a,
            "label": ACTION_LABELS.get(a, a.replace("_", " ").capitalize())
        }
        for a in raw_actions
    ]
    models = (
        HistoryEvent.objects.exclude(content_type=notification_ct)
        .values_list("content_type__model", flat=True).distinct().order_by("content_type__model")
    )

  

    # pagination
    paginator = Paginator(qs, 25)
    page_obj = paginator.get_page(request.GET.get("page"))

    # maak display velden + link naar object
    events = []
    for h in page_obj.object_list:
        actor_label = h.actor.username if h.actor_id else "Systeem"

        action_label = ACTION_LABELS.get(h.action, h.action.replace("_", " ").capitalize())
        model_name = h.content_type.model if h.content_type_id else "onbekend"

        url = None
        if model_name == "signal":
            url = f"/signals/{h.object_id}/"
        elif model_name == "task":
            url = f"/tasks/{h.object_id}/"
        elif model_name == "person":
            url = f"/people/{h.object_id}/"

        events.append({
            "id": h.id,
            "created_at": h.created_at,
            "actor_label": actor_label,
            "action": h.action,
            "action_label": action_label,
            "model": model_name,
            "object_id": h.object_id,
            "changes": h.changes,
            "url": url,
        })

    return render(request, "core/activities/list.html", {
        "page_obj": page_obj,
        "events": events,
        "q": q,
        "action": action,
        "model": model,
        "actions": actions,
        "models": models,
        "active_nav": "activities",
    })