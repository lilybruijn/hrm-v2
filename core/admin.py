from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline

from core.models import (
    Signal, Task, Note, HistoryEvent, Status, SignalType, TaskType, Notification, Person
)

class NoteInline(GenericTabularInline):
    model = Note
    extra = 0
    readonly_fields = ("author", "created_at")
    fields = ("author", "body", "created_at")

class HistoryInline(GenericTabularInline):
    model = HistoryEvent
    extra = 0
    readonly_fields = ("actor", "action", "changes", "created_at")
    fields = ("actor", "action", "changes", "created_at")
    can_delete = False

@admin.register(Signal)
class SignalAdmin(admin.ModelAdmin):
    inlines = [NoteInline, HistoryInline]
    list_display = ("id", "type", "assigned_to", "active_from", "status", "is_archived", "created_at")
    list_filter = ("type", "status", "is_archived")
    search_fields = ("body",)

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    inlines = [NoteInline, HistoryInline]
    list_display = ("id", "type", "assigned_to", "due_at", "status", "is_archived", "created_at")
    list_filter = ("type", "status", "is_archived")
    search_fields = ("body",)

# ✅ register “support” models too
@admin.register(Status)
class StatusAdmin(admin.ModelAdmin):
    list_display = ("scope", "name", "key", "is_default", "is_active", "sort_order")
    list_filter = ("scope", "is_active", "is_default")
    search_fields = ("name", "key")
    ordering = ("scope", "sort_order", "name")

@admin.register(SignalType)
class SignalTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "sort_order")
    list_filter = ("is_active",)
    search_fields = ("name",)

@admin.register(TaskType)
class TaskTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "sort_order")
    list_filter = ("is_active",)
    search_fields = ("name",)

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "type", "is_read", "created_at")
    list_filter = ("type", "is_read", "created_at")
    search_fields = ("title", "message", "user__username", "user__email")

@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ("id", "person_type", "last_name", "first_name", "email", "phone", "created_at")
    list_filter = ("person_type",)
    search_fields = ("first_name", "last_name", "email", "phone")

from django.contrib import admin
from core.models import Notification


