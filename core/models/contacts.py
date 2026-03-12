# core/models/contacts.py
from django.db import models


class ContactPerson(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)

    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    job_title = models.CharField(max_length=255, blank=True)

    organization = models.ForeignKey(
        "Organization",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="contact_people",
    )

    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["last_name", "first_name"]

    def __str__(self):
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
    
class PersonContact(models.Model):
    person = models.ForeignKey(
        "Person",
        on_delete=models.CASCADE,
        related_name="person_contacts",
    )
    contact_person = models.ForeignKey(
        "ContactPerson",
        on_delete=models.CASCADE,
        related_name="linked_people",
    )
    relation_type = models.ForeignKey(
        "SettingOption",
        on_delete=models.PROTECT,
        related_name="person_contact_relations",
        limit_choices_to={"category": "person_contact_relation_type"},
    )
    is_primary = models.BooleanField(default=False)
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ("person", "contact_person", "relation_type")

    def __str__(self):
        return f"{self.person.full_name} - {self.contact_person.full_name}"