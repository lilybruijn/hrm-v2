from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction


class Command(BaseCommand):
    help = "Seed minimal data (users + optionally core models if present). Safe to run early."

    def add_arguments(self, parser):
        parser.add_argument("--clear", action="store_true", help="Clear seeded data (best effort).")

    @transaction.atomic
    def handle(self, *args, **options):
        do_clear = options["clear"]

        # --- USERS ---
        User = get_user_model()

        admin, _ = User.objects.get_or_create(
            username="admin",
            defaults={"email": "lilybruijn1991@gmail.com", "is_staff": True, "is_superuser": True},
        )
        admin.is_staff = True
        admin.is_superuser = True
        admin.set_password("zandTermietjes")
        admin.save()

        emma, _ = User.objects.get_or_create(
            username="emma",
            defaults={"email": "emma@example.com", "is_staff": True, "is_superuser": False},
        )
        emma.is_staff = True
        emma.set_password("zandTermietjes")
        emma.save()

        self.stdout.write(self.style.SUCCESS("✅ Seeded users: admin / emma"))

        # --- OPTIONAL CORE SEEDS ---
        # Zodra jij straks models maakt zoals Status, SignalType, TaskType, etc,
        # kun je hier seeding aanzetten. Tot die tijd faalt dit niet.
        try:
            from core import models as m
        except Exception:
            self.stdout.write(self.style.WARNING("⚠️ core.models not importable yet. Skipping core seeds."))
            return

        # Best-effort clear (alleen als modellen bestaan)
        if do_clear:
            for name in ["Notification", "Task", "Signal", "Message", "Thread", "Status", "TaskType", "SignalType"]:
                Model = getattr(m, name, None)
                if Model:
                    Model.objects.all().delete()
            self.stdout.write(self.style.WARNING("🧹 Cleared core tables (best effort)."))

        # Voorbeeld: seed Status als model bestaat
        Status = getattr(m, "Status", None)
        if Status:
            for key, label, scope in [
                ("open", "Open", "signal"),
                ("done", "Afgerond", "signal"),
                ("snoozed", "Gepauzeerd", "signal"),
                ("todo", "Te doen", "task"),
                ("in_progress", "Bezig", "task"),
                ("completed", "Voltooid", "task"),
            ]:
                Status.objects.get_or_create(key=key, defaults={"label": label, "scope": scope})
            self.stdout.write(self.style.SUCCESS("✅ Seeded Status"))

        SignalType = getattr(m, "SignalType", None)
        if SignalType:
            SignalType.objects.get_or_create(name="Algemeen", defaults={"description": ""})
            SignalType.objects.get_or_create(name="Contract", defaults={"description": ""})
            self.stdout.write(self.style.SUCCESS("✅ Seeded SignalType"))

        TaskType = getattr(m, "TaskType", None)
        if TaskType:
            TaskType.objects.get_or_create(name="Opvolgen", defaults={"description": ""})
            TaskType.objects.get_or_create(name="Administratie", defaults={"description": ""})
            self.stdout.write(self.style.SUCCESS("✅ Seeded TaskType"))

        self.stdout.write(self.style.SUCCESS("✅ Seeding completed"))