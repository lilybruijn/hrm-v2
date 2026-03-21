from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

User = get_user_model()


class UserCreateForm(forms.ModelForm):
    password = forms.CharField(
        label="Wachtwoord",
        widget=forms.PasswordInput(attrs={"class": "form-control form-control-sm"}),
    )

    group = forms.ModelChoiceField(
        queryset=Group.objects.all().order_by("name"),
        required=False,
        empty_label="Geen groep",
        widget=forms.Select(attrs={"class": "form-select form-select-sm"}),
        label="Groep",
    )

    class Meta:
        model = User
        fields = ["username", "email", "is_staff", "is_superuser", "is_active"]
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control form-control-sm"}),
            "email": forms.EmailInput(attrs={"class": "form-control form-control-sm"}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])

        if commit:
            user.save()
            user.groups.clear()

            group = self.cleaned_data.get("group")
            if group:
                user.groups.add(group)

        return user


class UserUpdateForm(forms.ModelForm):
    password = forms.CharField(
        label="Nieuw wachtwoord",
        required=False,
        widget=forms.PasswordInput(attrs={"class": "form-control form-control-sm"}),
    )

    group = forms.ModelChoiceField(
        queryset=Group.objects.all().order_by("name"),
        required=False,
        empty_label="Geen groep",
        widget=forms.Select(attrs={"class": "form-select form-select-sm"}),
        label="Groep",
    )

    class Meta:
        model = User
        fields = ["username", "email", "is_staff", "is_superuser", "is_active"]
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control form-control-sm"}),
            "email": forms.EmailInput(attrs={"class": "form-control form-control-sm"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance.pk:
            self.fields["group"].initial = self.instance.groups.first()

    def save(self, commit=True):
        user = super().save(commit=False)

        password = self.cleaned_data.get("password")
        if password:
            user.set_password(password)

        if commit:
            user.save()
            user.groups.clear()

            group = self.cleaned_data.get("group")
            if group:
                user.groups.add(group)

        return user