# core/models/people.py
from django.db import models


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
    person = models.OneToOneField(
        "Person",
        on_delete=models.CASCADE,
        related_name="student_profile",
    )
    is_active_student = models.BooleanField(default=True)
    has_dropped_out = models.BooleanField(default=False)
    dropout_date = models.DateField(null=True, blank=True)
    dropout_reason = models.TextField(blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Studentprofiel van {self.person.full_name}"
    
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