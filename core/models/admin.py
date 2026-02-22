from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline

from core.models import (
    Signal, Task,
    Note, HistoryEvent,
    Status, SignalType, TaskType,
    Notification,
    Person,
)

# -------------------------
# Inlines (Generic)
# -------------------------

class NoteInline(GenericTabularInline):
    model = Note
    ct_field = "content_type"
    ct_fk_field = "object_id"
    extra = 0
    can_delete = True

    readonly_fields = ("author", "created_at")
    fields = ("author", "body", "created_at")

    autocomplete_fields = ("author",)


class HistoryInline(GenericTabularInline):
    model = HistoryEvent
    ct_field = "content_type"
    ct_fk_field = "object_id"
    extra = 0
    can_delete = False

    readonly_fields = ("actor", "action", "changes", "created_at")
    fields = ("actor", "action", "changes", "created_at")

    autocomplete_fields = ("actor",)


# -------------------------
# Core
# -------------------------

@admin.register(Signal)
class SignalAdmin(admin.ModelAdmin):
    inlines = [NoteInline, HistoryInline]
    list_display = ("id", "type", "assigned_to", "active_from", "status", "is_archived", "created_at")
    list_filter = ("type", "status", "is_archived")
    search_fields = ("body",)
    ordering = ("-active_from", "-created_at")
    autocomplete_fields = ("assigned_to", "type", "status")
    date_hierarchy = "active_from"


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    inlines = [NoteInline, HistoryInline]
    list_display = ("id", "type", "assigned_to", "due_at", "status", "is_archived", "created_at")
    list_filter = ("type", "status", "is_archived")
    search_fields = ("body",)
    ordering = ("-due_at", "-created_at")
    autocomplete_fields = ("assigned_to", "type", "status")
    date_hierarchy = "due_at"


# -------------------------
# Dictionaries / Config
# -------------------------

@admin.register(Status)
class StatusAdmin(admin.ModelAdmin):
    list_display = ("scope", "name", "key", "is_default", "is_active", "sort_order")
    list_filter = ("scope", "is_active", "is_default")
    search_fields = ("name", "key")
    ordering = ("scope", "sort_order", "name")
    list_editable = ("is_default", "is_active", "sort_order")


@admin.register(SignalType)
class SignalTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "sort_order")
    list_filter = ("is_active",)
    search_fields = ("name", "description")
    ordering = ("sort_order", "name")
    list_editable = ("is_active", "sort_order")


@admin.register(TaskType)
class TaskTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "sort_order")
    list_filter = ("is_active",)
    search_fields = ("name", "description")
    ordering = ("sort_order", "name")
    list_editable = ("is_active", "sort_order")


# -------------------------
# Notifications
# -------------------------

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "title", "is_read", "created_at")
    list_filter = ("is_read",)
    search_fields = ("title", "body", "url")
    ordering = ("is_read", "-created_at")
    autocomplete_fields = ("user",)

    # handig tijdens debuggen
    readonly_fields = ("created_at", "read_at")


# -------------------------
# People
# -------------------------

@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ("id", "person_type", "last_name", "first_name", "email", "phone", "created_at")
    list_filter = ("person_type",)
    search_fields = ("first_name", "last_name", "email", "phone")
    ordering = ("last_name", "first_name")