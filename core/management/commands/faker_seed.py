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
    help = "Seed database met faker data"

    def handle(self, *args, **options):
        self.stdout.write("Seeding gestart...")

        self.seed_groups()
        self.seed_setting_options()
        self.seed_statuses()
        self.seed_types()
        self.seed_users()

        people = self.seed_people()
        organizations = self.seed_organizations()
        signals = self.seed_signals(people)
        self.seed_contact_people(people, organizations)
        self.seed_tasks(people, signals)
        self.seed_jobcoaching_periods(people, organizations)
        self.seed_wage_value_periods(people, organizations)

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
                "email": "admin@example.com",
                "is_staff": True,
                "is_superuser": True,
                "is_active": True,
            },
        )
        admin_user.set_password("admin123")
        admin_user.save()
        admin_user.groups.set([admin_group])

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
            user.groups.set([user_group])
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
            ("busy", "Bezig"),
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

    def seed_people(self):
        people = []

        for _ in range(40):
            person_type = random.choice(["student", "employee"])

            person = Person.objects.create(
                person_type=person_type,
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                email=fake.email(),
                phone=fake.phone_number(),
                birth_date=fake.date_of_birth(minimum_age=16, maximum_age=67),
                bsn=str(fake.random_number(digits=9, fix_len=True)),
                street=fake.street_name(),
                house_number=str(fake.building_number()),
                postal_code=fake.postcode(),
                city=fake.city(),
                description=fake.paragraph(nb_sentences=3),
                status="active",
                is_archived=False,
            )
            people.append(person)

            if person_type == "employee":
                EmployeeProfile.objects.update_or_create(
                    person=person,
                    defaults={
                        "is_active_employee": True,
                        "notes": fake.sentence() if random.random() < 0.4 else "",
                    },
                )
            else:
                has_dropped_out = random.random() < 0.15

                StudentProfile.objects.update_or_create(
                    person=person,
                    defaults={
                        "is_active_student": not has_dropped_out,
                        "has_dropped_out": has_dropped_out,
                        "dropout_date": fake.date_between(start_date="-1y", end_date="today") if has_dropped_out else None,
                        "dropout_reason": fake.sentence() if has_dropped_out else "",
                        "notes": fake.sentence() if random.random() < 0.4 else "",
                    },
                )

        return people

    def seed_organizations(self):
        organization_types = list(
            SettingOption.objects.filter(category="organization_type", is_active=True)
        )

        organizations = []

        for _ in range(12):
            org = Organization.objects.create(
                name=fake.company(),
                organization_type=random.choice(organization_types),
                is_archived=random.random() < 0.1,
            )
            organizations.append(org)

        return organizations

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

    def seed_jobcoaching_periods(self, people, organizations):
        employee_people = [p for p in people if p.person_type == "employee"]
        jobcoaching_statuses = list(
            SettingOption.objects.filter(category="jobcoaching_status", is_active=True)
        )

        if not employee_people or not jobcoaching_statuses:
            return

        for _ in range(30):
            person = random.choice(employee_people)
            start_date = fake.date_between(start_date="-1y", end_date="today")

            end_date = (
                fake.date_between(start_date=start_date, end_date="+180d")
                if random.random() < 0.5 else None
            )

            JobCoachingPeriod.objects.create(
                person=person,
                organization=random.choice(organizations) if organizations else None,
                status=random.choice(jobcoaching_statuses),
                start_date=start_date,
                end_date=end_date,
                notes=fake.paragraph(nb_sentences=3),
                is_archived=random.random() < 0.1,
            )

    def seed_wage_value_periods(self, people, organizations):
        employee_people = [p for p in people if p.person_type == "employee"]
        wage_value_statuses = list(
            SettingOption.objects.filter(category="wage_value_status", is_active=True)
        )
        decision_statuses = list(
            SettingOption.objects.filter(category="wage_value_decision_status", is_active=True)
        )

        if not employee_people or not wage_value_statuses:
            return

        for _ in range(30):
            person = random.choice(employee_people)
            start_date = fake.date_between(start_date="-1y", end_date="today")

            end_date = (
                fake.date_between(start_date=start_date, end_date="+180d")
                if random.random() < 0.5 else None
            )

            meeting_date = (
                fake.date_between(start_date=start_date, end_date="today")
                if random.random() < 0.7 else None
            )

            WageValuePeriod.objects.create(
                person=person,
                organization=random.choice(organizations) if organizations else None,
                status=random.choice(wage_value_statuses),
                decision_status=random.choice(decision_statuses) if decision_statuses and random.random() < 0.8 else None,
                start_date=start_date,
                end_date=end_date,
                percentage=round(random.uniform(30, 100), 2),
                meeting_date=meeting_date,
                meeting_location=fake.company() if meeting_date else "",
                meeting_attendees=", ".join(fake.name() for _ in range(random.randint(1, 4))) if meeting_date else "",
                notes=fake.paragraph(nb_sentences=3),
                is_archived=random.random() < 0.1,
            )

    def seed_contact_people(self, people, organizations):
        relation_types = list(
            SettingOption.objects.filter(
                category="person_contact_relation_type",
                is_active=True,
            )
        )

        if not relation_types:
            return

        contact_people = []

        for _ in range(25):
            contact_person = ContactPerson.objects.create(
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                email=fake.email(),
                phone=fake.phone_number(),
                job_title=random.choice([
                    "Jobcoach",
                    "Begeleider",
                    "HR-adviseur",
                    "Manager",
                    "Ouder / verzorger",
                    "Contactpersoon",
                ]),
                organization=random.choice(organizations) if organizations and random.random() < 0.7 else None,
                notes=fake.paragraph(nb_sentences=2),
                is_active=random.random() < 0.9,
            )
            contact_people.append(contact_person)

        used_pairs = set()

        for person in random.sample(people, min(len(people), 30)):
            link_count = random.randint(1, 3)
            selected_contacts = random.sample(contact_people, min(link_count, len(contact_people)))

            first_link = True
            for contact_person in selected_contacts:
                relation_type = random.choice(relation_types)

                unique_key = (person.id, contact_person.id, relation_type.id)
                if unique_key in used_pairs:
                    continue
                used_pairs.add(unique_key)

                PersonContact.objects.create(
                    person=person,
                    contact_person=contact_person,
                    relation_type=relation_type,
                    is_primary=first_link,
                    notes=fake.sentence() if random.random() < 0.4 else "",
                )
                first_link = False