from django import forms
from django.urls import reverse
from django.utils.html import format_html

from core.models.people import Person


class PersonForm(forms.ModelForm):
    class Meta:
        model = Person
        fields = [
            "person_type",
            "first_name",
            "last_name",
            "birth_date",
            "bsn",
            "email",
            "phone",
            "street",
            "house_number",
            "postal_code",
            "city",
        ]
        widgets = {
            "person_type": forms.Select(attrs={"class": "form-select"}),
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "birth_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "bsn": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
            "street": forms.TextInput(attrs={"class": "form-control"}),
            "house_number": forms.TextInput(attrs={"class": "form-control"}),
            "postal_code": forms.TextInput(attrs={"class": "form-control"}),
            "city": forms.TextInput(attrs={"class": "form-control"}),
        }

    def clean(self):
        cleaned_data = super().clean()

        first_name = (cleaned_data.get("first_name") or "").strip()
        last_name = (cleaned_data.get("last_name") or "").strip()
        bsn = (cleaned_data.get("bsn") or "").strip()
        email = (cleaned_data.get("email") or "").strip().lower()
        phone = self.normalize_phone(cleaned_data.get("phone"))

        street = (cleaned_data.get("street") or "").strip()
        house_number = (cleaned_data.get("house_number") or "").strip()
        postal_code = (cleaned_data.get("postal_code") or "").strip().upper()
        city = (cleaned_data.get("city") or "").strip()

        cleaned_data["first_name"] = first_name
        cleaned_data["last_name"] = last_name
        cleaned_data["bsn"] = bsn
        cleaned_data["email"] = email
        cleaned_data["phone"] = phone
        cleaned_data["street"] = street
        cleaned_data["house_number"] = house_number
        cleaned_data["postal_code"] = postal_code
        cleaned_data["city"] = city

        def other_people():
            qs = Person.objects.all()
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            return qs

        def person_link(person):
            url = reverse("people:detail", args=[person.pk])
            return format_html('<a href="{}">{}</a>', url, person.full_name)

        # dubbele naam
        if first_name and last_name:
            conflict = other_people().filter(
                first_name__iexact=first_name,
                last_name__iexact=last_name,
            ).first()
            if conflict:
                self.add_error(
                    None,
                    format_html(
                        'Er bestaat al een persoon met deze naam. <strong>{}</strong>.',
                        person_link(conflict),
                    ),
                )

        # dubbele bsn
        if bsn:
            conflict = other_people().filter(bsn=bsn).first()
            if conflict:
                self.add_error(
                    "bsn",
                    format_html(
                        'Dit BSN bestaat al bij: <strong>{}</strong>.',
                        person_link(conflict),
                    ),
                )

        # dubbele email
        if email:
            conflict = other_people().filter(email__iexact=email).first()
            if conflict:
                self.add_error(
                    "email",
                    format_html(
                        'Dit e-mailadres bestaat al bij: <strong>{}</strong>.',
                        person_link(conflict),
                    ),
                )

        # dubbele telefoon
        if phone:
            for person in other_people().exclude(phone=""):
                existing_phone = self.normalize_phone(person.phone)
                if existing_phone and existing_phone == phone:
                    self.add_error(
                        "phone",
                        format_html(
                            'Dit telefoonnummer bestaat al bij: <strong>{}</strong>.',
                            person_link(person),
                        ),
                    )
                    break

        return cleaned_data

    @staticmethod
    def normalize_phone(value):
        value = (value or "").strip()

        if not value:
            return ""

        value = value.replace(" ", "")
        value = value.replace("-", "")
        value = value.replace("(", "")
        value = value.replace(")", "")
        value = value.replace(".", "")
        value = value.replace("/", "")

        if value.startswith("+31"):
            value = "0" + value[3:]
        elif value.startswith("31") and not value.startswith("310"):
            value = "0" + value[2:]

        return value