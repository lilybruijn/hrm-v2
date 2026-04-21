from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Prefetch, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from core.auth import staff_required
from core.models import InboxThread, InboxParticipant, InboxMessage

from .forms import InboxThreadForm, InboxReplyForm

User = get_user_model()


@staff_required
def thread_list(request):
    q = (request.GET.get("q") or "").strip()
    archived = (request.GET.get("archived") or "0").strip()
    unread_only = (request.GET.get("unread") or "").strip()

    qs = (
        InboxParticipant.objects
        .select_related("thread", "thread__created_by", "user")
        .filter(user=request.user)
        .prefetch_related(
            Prefetch(
                "thread__messages",
                queryset=InboxMessage.objects.select_related("sender").order_by("created_at"),
            ),
            Prefetch(
                "thread__participant_links",
                queryset=InboxParticipant.objects.select_related("user"),
            ),
        )
    )

    if archived == "1":
        qs = qs.filter(is_archived=True)
    else:
        qs = qs.filter(is_archived=False)

    if q:
        qs = qs.filter(
            Q(thread__subject__icontains=q)
            | Q(thread__messages__body__icontains=q)
            | Q(thread__messages__sender__username__icontains=q)
        ).distinct()

    qs = qs.order_by("-thread__updated_at", "-thread__created_at").distinct()

    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(request.GET.get("page"))

    visible_items = []
    for participation in page_obj.object_list:
        latest_message = participation.thread.latest_message
        participation.latest_message = latest_message
        participation.is_unread_flag = participation.is_unread

        if unread_only == "1" and not participation.is_unread_flag:
            continue

        other_participants = [
            link.user for link in participation.thread.participant_links.all()
            if link.user_id != request.user.id
        ]
        participation.other_participants = other_participants
        visible_items.append(participation)

    return render(request, "core/inbox/list.html", {
        "page_obj": page_obj,
        "threads": visible_items,
        "q": q,
        "archived": archived,
        "unread_only": unread_only,
        "active_nav": "inbox",
    })


@staff_required
@transaction.atomic
def thread_create(request):
    if request.method == "POST":
        form = InboxThreadForm(request.POST, user=request.user)
        if form.is_valid():
            thread = InboxThread.objects.create(
                subject=form.cleaned_data["subject"],
                created_by=request.user,
            )

            recipients = list(form.cleaned_data["recipients"])
            participants = [request.user, *recipients]

            seen_ids = set()
            unique_participants = []
            for user in participants:
                if user.id in seen_ids:
                    continue
                seen_ids.add(user.id)
                unique_participants.append(user)

            for user in unique_participants:
                InboxParticipant.objects.create(
                    thread=thread,
                    user=user,
                    last_read_at=timezone.now() if user == request.user else None,
                )

            InboxMessage.objects.create(
                thread=thread,
                sender=request.user,
                body=form.cleaned_data["body"],
            )

            messages.success(request, "Bericht verzonden.")
            return redirect("inbox:detail", pk=thread.pk)
    else:
        form = InboxThreadForm(user=request.user)

    return render(request, "core/inbox/form.html", {
        "form": form,
        "active_nav": "inbox",
    })


@staff_required
def thread_detail(request, pk: int):
    participation = get_object_or_404(
        InboxParticipant.objects.select_related("thread", "thread__created_by", "user"),
        thread_id=pk,
        user=request.user,
    )

    thread = participation.thread
    thread_messages = thread.messages.select_related("sender").order_by("created_at")
    participant_links = thread.participant_links.select_related("user").order_by("user__username")

    participation.last_read_at = timezone.now()
    participation.save(update_fields=["last_read_at"])

    return render(request, "core/inbox/detail.html", {
        "thread": thread,
        "messages_list": thread_messages,
        "participant_links": participant_links,
        "reply_form": InboxReplyForm(),
        "active_nav": "inbox",
    })


@staff_required
@require_POST
@transaction.atomic
def thread_reply(request, pk: int):
    participation = get_object_or_404(
        InboxParticipant,
        thread_id=pk,
        user=request.user,
    )

    form = InboxReplyForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Bericht is niet geldig.")
        return redirect("inbox:detail", pk=pk)

    InboxMessage.objects.create(
        thread=participation.thread,
        sender=request.user,
        body=form.cleaned_data["body"],
    )

    participation.last_read_at = timezone.now()
    participation.save(update_fields=["last_read_at"])

    messages.success(request, "Antwoord verzonden.")
    return redirect("inbox:detail", pk=pk)


@staff_required
@require_POST
@transaction.atomic
def thread_toggle_archive(request, pk: int):
    participation = get_object_or_404(
        InboxParticipant,
        thread_id=pk,
        user=request.user,
    )

    participation.is_archived = not participation.is_archived
    participation.save(update_fields=["is_archived"])

    messages.success(request, "Archiefstatus bijgewerkt.")
    return redirect("inbox:list")


@staff_required
@require_POST
@transaction.atomic
def thread_mark_read(request, pk: int):
    participation = get_object_or_404(
        InboxParticipant,
        thread_id=pk,
        user=request.user,
    )

    participation.last_read_at = timezone.now()
    participation.save(update_fields=["last_read_at"])

    messages.success(request, "Gesprek gemarkeerd als gelezen.")
    return redirect("inbox:list")


@staff_required
@require_POST
@transaction.atomic
def thread_mark_unread(request, pk: int):
    participation = get_object_or_404(
        InboxParticipant,
        thread_id=pk,
        user=request.user,
    )

    participation.last_read_at = None
    participation.save(update_fields=["last_read_at"])

    messages.success(request, "Gesprek gemarkeerd als ongelezen.")
    return redirect("inbox:list")