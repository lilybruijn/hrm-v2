from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from faker import Faker
import random

from core.models import (
    Person,
    EmployeeProfile,
    StudentProfile,
    Status,
    SignalType,
    TaskType,
    Signal,
    Task,
    SettingOption,
    Organization,
    JobCoachingPeriod,
    WageValuePeriod,
    ContactPerson,
    PersonContact,
)

User = get_user_model()
fake = Faker("nl_NL")


class Command(BaseCommand):
    help = "Seed database met default data"

    def handle(self, *args, **options):
        self.stdout.write("Seeding gestart...")

        self.seed_groups()
        self.seed_setting_options()
        self.seed_statuses()
        self.seed_types()
        self.seed_users()



        self.stdout.write(self.style.SUCCESS("Seeding klaar."))

    def seed_groups(self):
        self.stdout.write("Seeding groups...")

        admin_group, _ = Group.objects.get_or_create(name="admin")
        superuser_group, _ = Group.objects.get_or_create(name="superuser")
        user_group, _ = Group.objects.get_or_create(name="gebruiker")
        viewer_group, _ = Group.objects.get_or_create(name="bekijker")

        all_permissions = Permission.objects.all()

        admin_group.permissions.set(all_permissions)
        superuser_group.permissions.set(all_permissions)

        user_permissions = Permission.objects.exclude(codename__startswith="delete_")
        user_group.permissions.set(user_permissions)

        viewer_permissions = Permission.objects.filter(codename__startswith="view_")
        viewer_group.permissions.set(viewer_permissions)

        self.stdout.write(self.style.SUCCESS("Groups en permissions aangemaakt."))

    def seed_users(self):
        admin_group = Group.objects.get(name="admin")
        user_group = Group.objects.get(name="gebruiker")

        admin_user, _ = User.objects.update_or_create(
            username="admin",
            defaults={
                "email": "lily-bruijn@prems.work",
                "is_staff": True,
                "is_superuser": True,
                "is_active": True,
            },
        )
        admin_user.set_password("zandTermietjes")
        admin_user.save()
        admin_user.groups.set([admin_group])

    def seed_setting_options(self):
        options = [
            ("organization_type", "municipality", "Gemeente", 1),
            ("organization_type", "uwv", "UWV", 2),
            ("organization_type", "employer", "Werkgever", 3),
            ("organization_type", "other", "Overig", 99),

            ("person_contact_relation_type", "municipality_contact", "Gemeentelijk contactpersoon", 1),
            ("person_contact_relation_type", "uwv_contact", "UWV-contactpersoon", 2),
            ("person_contact_relation_type", "employer_contact", "Werkgever contactpersoon", 3),
            ("person_contact_relation_type", "parent_guardian", "Ouder / verzorger", 4),
            ("person_contact_relation_type", "other", "Overig", 99),

            ("document_type", "employment_contract", "Arbeidsovereenkomst", 1),
            ("document_type", "jobcoach_request", "Jobcoachaanvraag", 2),
            ("document_type", "wage_value", "Loonwaardeformulier", 3),
            ("document_type", "report", "Rapportage", 4),
            ("document_type", "settlement_agreement", "Vaststellingsovereenkomst", 5),
            ("document_type", "other", "Overig", 99),

            ("jobcoaching_status", "draft", "Concept", 1),
            ("jobcoaching_status", "requested", "Aangevraagd", 2),
            ("jobcoaching_status", "active", "Lopend", 3),
            ("jobcoaching_status", "completed", "Afgerond", 4),
            ("jobcoaching_status", "rejected", "Afgewezen", 5),

            ("wage_value_status", "preparation", "Voorbereiding", 1),
            ("wage_value_status", "meeting_planned", "Gesprek gepland", 2),
            ("wage_value_status", "meeting_done", "Gesprek gehad", 3),
            ("wage_value_status", "awaiting_decision", "Beschikking afwachten", 4),
            ("wage_value_status", "completed", "Afgerond", 5),

            ("wage_value_decision_status", "pending", "In afwachting", 1),
            ("wage_value_decision_status", "received", "Beschikking ontvangen", 2),
            ("wage_value_decision_status", "rejected", "Afgewezen", 3),
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
            ("busy", "In behandeling"),
            ("done", "Afgerond"),
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