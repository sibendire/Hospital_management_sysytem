
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

        labels = {
            "name": "Test Name",
            "category": "Category",
            "price": "Price (UGX)",
            "description": "Description",
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

        labels = {
            "patient": "Patient",
            "test": "Laboratory Test",
        }

    def __init__(self, *args, **kwargs):

        super().__init__(
            *args,
            **kwargs
        )

        # -------------------------------------------------
        # PATIENT DROPDOWN
        # -------------------------------------------------

        self.fields["patient"].label_from_instance = (
            lambda patient:
            (
                f"{patient.patient_number} - "
                f"{patient.first_name} "
                f"{patient.last_name}"
            )
        )

        # -------------------------------------------------
        # LABORATORY TEST DROPDOWN
        # -------------------------------------------------

        self.fields["test"].label_from_instance = (
            lambda test:
            (
                f"{test.name} — "
                f"{test.category} — "
                f"UGX {test.price:,.0f}"
            )
        )

        # -------------------------------------------------
        # ORDERING
        # -------------------------------------------------

        self.fields["patient"].queryset = (
            self.fields["patient"]
            .queryset
            .order_by(
                "first_name",
                "last_name"
            )
        )

        self.fields["test"].queryset = (
            self.fields["test"]
            .queryset
            .order_by(
                "name"
            )
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
                    "placeholder": (
                        "Enter laboratory findings"
                    ),
                }
            ),

            "interpretation": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": (
                        "Enter medical interpretation"
                    ),
                }
            ),
        }

        labels = {
            "result": "Laboratory Result",
            "interpretation": "Clinical Interpretation",
        }

    def clean_result(self):

        result = self.cleaned_data.get(
            "result"
        )

        if result:

            result = result.strip()

        if not result:

            raise forms.ValidationError(
                "Laboratory result cannot be empty."
            )

        return result

    def clean_interpretation(self):

        interpretation = self.cleaned_data.get(
            "interpretation"
        )

        if interpretation:

            interpretation = interpretation.strip()

        return interpretation

