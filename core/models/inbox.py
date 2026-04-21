from django.conf import settings
from django.db import models
from django.utils import timezone

from .base import TimeStampedModel


class InboxThread(TimeStampedModel):
    subject = models.CharField(max_length=255)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_inbox_threads",
    )
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through="InboxParticipant",
        related_name="inbox_threads",
    )

    class Meta:
        ordering = ["-updated_at", "-created_at"]
        verbose_name = "inbox thread"
        verbose_name_plural = "inbox threads"

    def __str__(self):
        return self.subject

    @property
    def latest_message(self):
        return self.messages.select_related("sender").order_by("-created_at").first()


class InboxParticipant(models.Model):
    thread = models.ForeignKey(
        InboxThread,
        on_delete=models.CASCADE,
        related_name="participant_links",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="inbox_participations",
    )
    is_archived = models.BooleanField(default=False)
    last_read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("thread", "user")
        verbose_name = "inbox participant"
        verbose_name_plural = "inbox participants"

    def __str__(self):
        return f"{self.user} in {self.thread}"

    @property
    def is_unread(self):
        latest = self.thread.latest_message
        if not latest:
            return False
        if latest.sender_id == self.user_id:
            return False
        if not self.last_read_at:
            return True
        return latest.created_at > self.last_read_at


class InboxMessage(TimeStampedModel):
    thread = models.ForeignKey(
        InboxThread,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="sent_inbox_messages",
    )
    body = models.TextField()

    class Meta:
        ordering = ["created_at"]
        verbose_name = "inbox message"
        verbose_name_plural = "inbox messages"

    def __str__(self):
        return f"Bericht van {self.sender} in {self.thread}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        InboxThread.objects.filter(pk=self.thread_id).update(updated_at=timezone.now())