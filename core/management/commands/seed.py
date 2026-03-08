from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from faker import Faker
import random

from core.models import Person, Status, SignalType, TaskType, Signal, Task

User = get_user_model()
fake = Faker("nl_NL")


class Command(BaseCommand):
    help = "Seed database met faker data"

    def handle(self, *args, **options):
        self.stdout.write("Seeding gestart...")

        # =====================
        # USERS
        # =====================
        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser(
                username="admin",
                email="admin@hrm.local",
                password="admin123"
            )

        staff_users = []
        for i in range(5):
            u, _ = User.objects.get_or_create(
                username=f"staff{i+1}",
                defaults={
                    "email": fake.email(),
                    "is_staff": True,
                    "is_active": True,
                }
            )
            u.set_password("test1234")
            u.save()
            staff_users.append(u)

        # =====================
        # STATUSES
        # =====================
        signal_statuses = [
            ("new", "Nieuw"),
            ("in_progress", "In behandeling"),
            ("done", "Afgerond"),
        ]

        for i, (key, name) in enumerate(signal_statuses):
            Status.objects.get_or_create(
                scope="signal",
                key=key,
                defaults={
                    "name": name,
                    "is_active": True,
                    "sort_order": i,
                }
            )

        task_statuses = [
            ("open", "Open"),
            ("busy", "Bezig"),
            ("done", "Klaar"),
        ]

        for i, (key, name) in enumerate(task_statuses):
            Status.objects.get_or_create(
                scope="task",
                key=key,
                defaults={
                    "name": name,
                    "is_active": True,
                    "sort_order": i,
                }
            )

        # =====================
        # TYPES
        # =====================
        signal_types = ["Incident", "Ziekmelding", "Gesprek", "Klacht"]
        task_types = ["Bellen", "Mailen", "Afspraak", "Controle"]

        for i, name in enumerate(signal_types):
            SignalType.objects.get_or_create(
                name=name,
                defaults={"is_active": True, "sort_order": i}
            )

        for i, name in enumerate(task_types):
            TaskType.objects.get_or_create(
                name=name,
                defaults={"is_active": True, "sort_order": i}
            )

        # =====================
        # PERSONEN
        # =====================
        people = []
        for _ in range(40):
            p = Person.objects.create(
                person_type=random.choice(["student", "employee"]),
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                email=fake.email(),
                phone=fake.phone_number(),
                description=fake.paragraph(nb_sentences=3),
            )
            people.append(p)

        # =====================
        # SIGNALEN
        # =====================
        signal_status_list = list(Status.objects.filter(scope="signal"))
        signal_type_list = list(SignalType.objects.all())

        signals = []
        for _ in range(25):
            s = Signal.objects.create(
                name=fake.sentence(nb_words=4),
                type=random.choice(signal_type_list),
                status=random.choice(signal_status_list),
                assigned_to=random.choice(staff_users),
                active_from=fake.date_between(start_date="-1y", end_date="today"),
                body=fake.text(max_nb_chars=400),
            )

            # koppel random personen
            s.people.set(random.sample(people, random.randint(1, 4)))
            signals.append(s)

        # =====================
        # TASKS
        # =====================
        task_status_list = list(Status.objects.filter(scope="task"))
        task_type_list = list(TaskType.objects.all())

        for _ in range(60):
            t = Task.objects.create(
                type=random.choice(task_type_list),
                status=random.choice(task_status_list),
                assigned_to=random.choice(staff_users),
                due_at=fake.date_between(start_date="today", end_date="+60d"),
                body=fake.text(max_nb_chars=200),
                signal=random.choice(signals),
            )

            # zelfde people als signal OF random
            if random.random() < 0.7 and t.signal:
                t.people.set(t.signal.people.all())
            else:
                t.people.set(random.sample(people, random.randint(1, 3)))

        self.stdout.write(self.style.SUCCESS("Seeding klaar."))