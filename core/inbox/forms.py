from django import forms
from django.contrib.auth import get_user_model

from core.models import InboxThread, InboxMessage

User = get_user_model()


class InboxThreadForm(forms.ModelForm):
    recipients = forms.ModelMultipleChoiceField(
        queryset=User.objects.none(),
        required=True,
        label="Ontvangers",
        widget=forms.SelectMultiple(attrs={"class": "form-select js-multiselect"}),
    )
    body = forms.CharField(
        label="Bericht",
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 6}),
    )

    class Meta:
        model = InboxThread
        fields = ["subject"]
        widgets = {
            "subject": forms.TextInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        qs = User.objects.filter(is_staff=True, is_active=True).order_by("username")
        if user is not None:
            qs = qs.exclude(pk=user.pk)

        self.fields["recipients"].queryset = qs


class InboxReplyForm(forms.ModelForm):
    class Meta:
        model = InboxMessage
        fields = ["body"]
        widgets = {
            "body": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Typ je antwoord...",
                }
            )
        }