from django.db import models
from datetime import timedelta
from django.utils import timezone

class Person(models.Model):
    PERSON_TYPE_CHOICES = [
        ("student", "Student"),
        ("employee", "Medewerker"),
    ]

    person_type = models.CharField(max_length=20, choices=PERSON_TYPE_CHOICES, default="student")

    PERSON_STATUS_CHOICES = [
        ("active", "Actief"),
        ("inactive", "Inactief"),
        ("dropped_out", "Afgevallen"),
    ]

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    bsn = models.CharField(max_length=9, blank=True)
    street = models.CharField(max_length=255, blank=True)
    house_number = models.CharField(max_length=20, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    city = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=PERSON_STATUS_CHOICES,
        default="active",
    )
    is_archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["last_name", "first_name"]

    def __str__(self):
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

class StudentProfile(models.Model):
    INVOICE_STATUS_CHOICES = [
        ("offerte", "Offerte"),
        ("offerte_akkoord", "Offerte akkoord"),
        ("factuur_verstuurd", "Factuur verstuurd"),
        ("factuur_betaald", "Factuur betaald"),
    ]

    person = models.OneToOneField(
        "Person",
        on_delete=models.CASCADE,
        related_name="student_profile",
    )

    is_active_student = models.BooleanField(default=True)
    has_dropped_out = models.BooleanField(default=False)
    dropout_date = models.DateField(null=True, blank=True)
    dropout_reason = models.TextField(blank=True)

    trajectory_start_date = models.DateField(null=True, blank=True)
    trajectory_end_date = models.DateField(null=True, blank=True)

    has_diploma = models.BooleanField(default=False)
    has_job_guarantee = models.BooleanField(default=False)

    invoice_number = models.CharField(max_length=100, blank=True)
    invoice_sent_date = models.DateField(null=True, blank=True)
    invoice_paid_date = models.DateField(null=True, blank=True)
    invoice_status = models.CharField(
        max_length=30,
        choices=INVOICE_STATUS_CHOICES,
        blank=True,
    )

    notes = models.TextField(blank=True)

    @property
    def is_almost_finished(self):
        if self.has_dropped_out or not self.trajectory_end_date:
            return False

        today = timezone.localdate()
        return today <= self.trajectory_end_date <= (today + timedelta(days=30))

class EmployeeProfile(models.Model):
    person = models.OneToOneField(
        "Person",
        on_delete=models.CASCADE,
        related_name="employee_profile",
    )
    is_active_employee = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Medewerkerprofiel van {self.person.full_name}"