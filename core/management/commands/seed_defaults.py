from django.core.management.base import BaseCommand
from django.db import transaction

from core.models import StatusSet, Status, StatusUsage, SignalType, TaskType


class Command(BaseCommand):
    help = "Seed default StatusSets/Statuses/StatusUsage + basic types."

    @transaction.atomic
    def handle(self, *args, **options):
        # StatusSets
        signals_set, _ = StatusSet.objects.get_or_create(key="signals", defaults={"name": "Signals", "enabled": True})
        tasks_set, _ = StatusSet.objects.get_or_create(key="tasks", defaults={"name": "Tasks", "enabled": True})

        # StatusUsage (default ON)
        StatusUsage.objects.update_or_create(
            module_key="signals",
            defaults={"enabled": True, "status_set": signals_set},
        )
        StatusUsage.objects.update_or_create(
            module_key="tasks",
            defaults={"enabled": True, "status_set": tasks_set},
        )

        # helper
        def ensure_status(status_set: StatusSet, key: str, label: str, sort: int, is_done=False, is_default=False):
            obj, created = Status.objects.get_or_create(
                status_set=status_set,
                key=key,
                defaults={
                    "label": label,
                    "sort_order": sort,
                    "is_done": is_done,
                    "is_default": is_default,
                }
            )
            # update basics if already exists
            changed = False
            for field, val in {
                "label": label,
                "sort_order": sort,
                "is_done": is_done,
            }.items():
                if getattr(obj, field) != val:
                    setattr(obj, field, val)
                    changed = True
            if changed:
                obj.save()

            return obj

        # Signals statuses
        open_s = ensure_status(signals_set, "open", "Open", 10, is_done=False, is_default=True)
        done_s = ensure_status(signals_set, "done", "Afgerond", 90, is_done=True, is_default=False)

        # Make sure only one default per set
        Status.objects.filter(status_set=signals_set).exclude(id=open_s.id).update(is_default=False)

        # Tasks statuses
        todo = ensure_status(tasks_set, "todo", "Te doen", 10, is_done=False, is_default=True)
        done_t = ensure_status(tasks_set, "done", "Afgerond", 90, is_done=True, is_default=False)
        Status.objects.filter(status_set=tasks_set).exclude(id=todo.id).update(is_default=False)

        # Basic types
        SignalType.objects.get_or_create(name="Algemeen", defaults={"description": ""})
        TaskType.objects.get_or_create(name="Algemeen", defaults={"description": ""})

        self.stdout.write(self.style.SUCCESS("Seed defaults done."))