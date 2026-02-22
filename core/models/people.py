from django.db import models

class Person(models.Model):
    PERSON_TYPE_CHOICES = [
        ("student", "Student"),
        ("employee", "Medewerker"),
    ]

    person_type = models.CharField(max_length=20, choices=PERSON_TYPE_CHOICES, default="student")

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=150)

    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)

    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["last_name", "first_name"]

    def __str__(self):
        return f"{self.first_name} {self.last_name}"