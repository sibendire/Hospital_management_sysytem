from django import forms
from .models import Patient


class PatientForm(forms.ModelForm):

    class Meta:
        model = Patient

        fields = [
            "first_name",
            "last_name",
            "gender",
            "date_of_birth",
            "national_id",
            "phone",
            "email",
            "address",
            "blood_group",
            "photo",
            "next_of_kin",
            "next_of_kin_phone",
        ]

        widgets = {

            "first_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "First Name"
            }),

            "last_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Last Name"
            }),

            "gender": forms.Select(attrs={
                "class": "form-select"
            }),

            "date_of_birth": forms.DateInput(attrs={
                "class": "form-control",
                "type": "date"
            }),

            "national_id": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "National ID"
            }),

            "phone": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Phone Number"
            }),

            "email": forms.EmailInput(attrs={
                "class": "form-control",
                "placeholder": "Email Address"
            }),

            "address": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Address"
            }),

            "blood_group": forms.Select(attrs={
                "class": "form-select"
            }),

            "photo": forms.FileInput(attrs={
                "class": "form-control"
            }),

            "next_of_kin": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Next of Kin"
            }),

            "next_of_kin_phone": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Next of Kin Phone"
            }),
        }