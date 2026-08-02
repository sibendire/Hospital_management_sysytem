from django import forms
from .models import Patient

class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = "__all__"

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

            "patient_number": forms.TextInput(attrs={
                "class": "form-control"
            }),

            "national_id": forms.TextInput(attrs={
                "class": "form-control"
            }),

            "phone": forms.TextInput(attrs={
                "class": "form-control"
            }),

            "email": forms.EmailInput(attrs={
                "class": "form-control"
            }),

            "address": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3
            }),

            "blood_group": forms.Select(attrs={
                "class": "form-select"
            }),

            "photo": forms.FileInput(attrs={
                "class": "form-control"
            }),

            "next_of_kin": forms.TextInput(attrs={
                "class": "form-control"
            }),

            "next_of_kin_phone": forms.TextInput(attrs={
                "class": "form-control"
            }),
        }