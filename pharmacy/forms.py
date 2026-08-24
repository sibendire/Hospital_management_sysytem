from django import forms
from django.utils import timezone

from .models import (
    Medicine,
    Prescription,
    PrescriptionItem,
)


# =========================================================
# MEDICINE FORM
# =========================================================

class MedicineForm(forms.ModelForm):

    class Meta:

        model = Medicine

        fields = [
            "name",
            "generic_name",
            "brand_name",
            "category",
            "dosage_form",
            "strength",
            "unit",
            "manufacturer",
            "supplier",
            "batch_number",
            "expiry_date",
            "quantity",
            "reorder_level",
            "unit_price",
            "prescription_required",
            "status",
            "description",
        ]

        widgets = {

            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "e.g. Amoxicillin"
                }
            ),

            "generic_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "e.g. Amoxicillin Trihydrate"
                }
            ),

            "brand_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "e.g. Amoxil"
                }
            ),

            "category": forms.Select(
                attrs={
                    "class": "form-select"
                }
            ),

            "dosage_form": forms.Select(
                attrs={
                    "class": "form-select"
                }
            ),

            "strength": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "e.g. 500 mg"
                }
            ),

            "unit": forms.Select(
                attrs={
                    "class": "form-select"
                }
            ),

            "manufacturer": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Manufacturer"
                }
            ),

            "supplier": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Supplier / Distributor"
                }
            ),

            "batch_number": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "e.g. AMX2026A01"
                }
            ),

            "expiry_date": forms.DateInput(
                format="%Y-%m-%d",
                attrs={
                    "type": "date",
                    "class": "form-control"
                }
            ),

            "quantity": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": "0"
                }
            ),

            "reorder_level": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": "0"
                }
            ),

            "unit_price": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": "0",
                    "step": "0.01"
                }
            ),

            "prescription_required": forms.Select(
                attrs={
                    "class": "form-select"
                }
            ),

            "status": forms.Select(
                attrs={
                    "class": "form-select"
                }
            ),

            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Additional information..."
                }
            ),
        }

    def clean_expiry_date(self):

        expiry_date = self.cleaned_data.get(
            "expiry_date"
        )

        if (
            expiry_date
            and expiry_date < timezone.now().date()
        ):

            raise forms.ValidationError(
                "A new medicine cannot have an expiry date "
                "in the past."
            )

        return expiry_date

    def clean(self):

        cleaned_data = super().clean()

        quantity = cleaned_data.get("quantity")
        reorder_level = cleaned_data.get("reorder_level")

        if (
            quantity is not None
            and reorder_level is not None
            and reorder_level > quantity
        ):
            # Allowed because reorder level can be
            # higher than the current stock.
            pass

        return cleaned_data


# =========================================================
# PRESCRIPTION FORM
# =========================================================

class PrescriptionForm(forms.ModelForm):

    class Meta:

        model = Prescription

        fields = [
            "patient",
            "diagnosis",
            "notes",
        ]

        widgets = {

            "patient": forms.Select(
                attrs={
                    "class": "form-select"
                }
            ),

            "diagnosis": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Enter diagnosis..."
                }
            ),

            "notes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Additional notes..."
                }
            ),
        }


# =========================================================
# PRESCRIPTION ITEM FORM
# =========================================================

class PrescriptionItemForm(forms.ModelForm):

    class Meta:

        model = PrescriptionItem

        fields = [
            "medicine",
            "dosage",
            "frequency",
            "duration",
            "quantity",
            "instructions",
        ]

        widgets = {

            "medicine": forms.Select(
                attrs={
                    "class": "form-select"
                }
            ),

            "dosage": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "e.g. 500mg"
                }
            ),

            "frequency": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "e.g. 3 times daily"
                }
            ),

            "duration": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "e.g. 5 days"
                }
            ),

            "quantity": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 1
                }
            ),

            "instructions": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 2,
                    "placeholder": "e.g. Take after meals"
                }
            ),
        }