from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from faker import Faker
import random

from core.models import (
    Person,
    Status,
    SignalType,
    TaskType,
    Signal,
    Task,
    SettingOption,
)

User = get_user_model()
fake = Faker("nl_NL")


class Command(BaseCommand):
    help = "Seed database met faker data"

    def handle(self, *args, **options):
        self.stdout.write("Seeding gestart...")

        self.seed_users()
        self.seed_setting_options()
        self.seed_statuses()
        self.seed_types()

        people = self.seed_people()
        signals = self.seed_signals(people)
        self.seed_tasks(people, signals)

        self.stdout.write(self.style.SUCCESS("Seeding klaar."))

    def seed_users(self):
        admin_user, _ = User.objects.update_or_create(
            username="admin",
            defaults={
                "email": "admin@example.com",
                "is_staff": True,
                "is_superuser": True,
                "is_active": True,
            },
        )
        admin_user.set_password("admin123")
        admin_user.save()

        self.staff_users = []
        for i in range(5):
            user, _ = User.objects.update_or_create(
                username=f"staff{i + 1}",
                defaults={
                    "email": fake.email(),
                    "is_staff": True,
                    "is_active": True,
                },
            )
            user.set_password("test1234")
            user.save()
            self.staff_users.append(user)

    def seed_setting_options(self):
        options = [
            ("organization_type", "municipality", "Gemeente", 1),
            ("organization_type", "uwv", "UWV", 2),
            ("organization_type", "employer", "Werkgever", 3),
            ("organization_type", "school", "Opleider", 4),
            ("organization_type", "care_partner", "Zorgpartner", 5),
            ("organization_type", "other", "Overig", 99),
            ("person_contact_relation_type", "external_contact", "Extern contactpersoon", 1),
            ("person_contact_relation_type", "municipality_contact", "Gemeentelijk contactpersoon", 2),
            ("person_contact_relation_type", "uwv_contact", "UWV-contactpersoon", 3),
            ("person_contact_relation_type", "employer_contact", "Werkgever contactpersoon", 4),
            ("person_contact_relation_type", "parent_guardian", "Ouder / verzorger", 5),
            ("person_contact_relation_type", "other", "Overig", 99),
            ("document_type", "employment_contract", "Arbeidsovereenkomst", 1),
            ("document_type", "jobcoach_request", "Jobcoachaanvraag", 2),
            ("document_type", "wage_value", "Loonwaardeformulier", 3),
            ("document_type", "report", "Rapportage", 4),
            ("document_type", "settlement_agreement", "Vaststellingsovereenkomst", 5),
            ("document_type", "other", "Overig", 99),
        ]

        for category, code, label, sort_order in options:
            SettingOption.objects.update_or_create(
                category=category,
                code=code,
                defaults={
                    "label": label,
                    "sort_order": sort_order,
                    "is_active": True,
                },
            )

    def seed_statuses(self):
        signal_statuses = [
            ("new", "Nieuw"),
            ("in_progress", "In behandeling"),
            ("done", "Afgerond"),
        ]

        for i, (key, name) in enumerate(signal_statuses):
            Status.objects.update_or_create(
                scope="signal",
                key=key,
                defaults={
                    "name": name,
                    "is_active": True,
                    "sort_order": i,
                },
            )

        task_statuses = [
            ("open", "Open"),
            ("busy", "Bezig"),
            ("done", "Klaar"),
        ]

        for i, (key, name) in enumerate(task_statuses):
            Status.objects.update_or_create(
                scope="task",
                key=key,
                defaults={
                    "name": name,
                    "is_active": True,
                    "sort_order": i,
                },
            )

    def seed_types(self):
        signal_types = ["Incident", "Ziekmelding", "Gesprek", "Klacht"]
        task_types = ["Bellen", "Mailen", "Afspraak", "Controle"]

        for i, name in enumerate(signal_types):
            SignalType.objects.update_or_create(
                name=name,
                defaults={
                    "is_active": True,
                    "sort_order": i,
                },
            )

        for i, name in enumerate(task_types):
            TaskType.objects.update_or_create(
                name=name,
                defaults={
                    "is_active": True,
                    "sort_order": i,
                },
            )

    def seed_people(self):
        people = []

        for _ in range(40):
            person = Person.objects.create(
                person_type=random.choice(["student", "employee"]),
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                email=fake.email(),
                phone=fake.phone_number(),
                description=fake.paragraph(nb_sentences=3),
            )
            people.append(person)

        return people

    def seed_signals(self, people):
        signal_status_list = list(Status.objects.filter(scope="signal"))
        signal_type_list = list(SignalType.objects.all())

        signals = []

        for _ in range(25):
            signal = Signal.objects.create(
                name=fake.sentence(nb_words=4),
                type=random.choice(signal_type_list),
                status=random.choice(signal_status_list),
                assigned_to=random.choice(self.staff_users),
                active_from=fake.date_between(start_date="-1y", end_date="today"),
                body=fake.text(max_nb_chars=400),
            )
            signal.people.set(random.sample(people, random.randint(1, 4)))
            signals.append(signal)

        return signals

    def seed_tasks(self, people, signals):
        task_status_list = list(Status.objects.filter(scope="task"))
        task_type_list = list(TaskType.objects.all())

        for _ in range(60):
            task = Task.objects.create(
                type=random.choice(task_type_list),
                status=random.choice(task_status_list),
                assigned_to=random.choice(self.staff_users),
                due_at=fake.date_between(start_date="today", end_date="+60d"),
                body=fake.text(max_nb_chars=200),
                signal=random.choice(signals),
            )

            if random.random() < 0.7 and task.signal:
                task.people.set(task.signal.people.all())
            else:
                task.people.set(random.sample(people, random.randint(1, 3)))