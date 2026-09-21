from django import forms

from .models import (
    LabTest,
    LabRequest,
    LabResult,
)


# =========================================================
# LABORATORY TEST FORM
# =========================================================

class LabTestForm(forms.ModelForm):

    class Meta:

        model = LabTest

        fields = [
            "name",
            "category",
            "price",
            "description",
        ]

        widgets = {

            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter laboratory test name",
                }
            ),

            "category": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),

            "price": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter price",
                    "step": "0.01",
                    "min": "0",
                }
            ),

            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Enter test description",
                }
            ),
        }


# =========================================================
# LABORATORY REQUEST FORM
# =========================================================

class LabRequestForm(forms.ModelForm):

    class Meta:

        model = LabRequest

        fields = [
            "patient",
            "test",
        ]

        widgets = {

            "patient": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),

            "test": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
        }

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        # Improve the laboratory test dropdown.
        self.fields["test"].label_from_instance = (
            lambda test:
            f"{test.name} — {test.category} — "
            f"UGX {test.price:,.0f}"
        )


# =========================================================
# LABORATORY RESULT FORM
# =========================================================

class LabResultForm(forms.ModelForm):

    class Meta:

        model = LabResult

        fields = [
            "result",
            "interpretation",
        ]

        widgets = {

            "result": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 5,
                    "placeholder": "Enter laboratory findings",
                }
            ),

            "interpretation": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Enter medical interpretation",
                }
            ),
        }