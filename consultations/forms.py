from django import forms

from .models import (
    ClinicalEncounter,
    VitalSigns,
    Diagnosis,
)

from laboratory.models import LabTest


# =========================================================
# CLINICAL ENCOUNTER FORM
# =========================================================

class ClinicalEncounterForm(forms.ModelForm):

    class Meta:

        model = ClinicalEncounter

        fields = [
            "encounter_type",
            "chief_complaint",
            "history_of_present_illness",
            "clinical_examination",
            "assessment",
            "treatment_plan",
            "clinical_notes",
            "follow_up_date",
            "follow_up_instructions",
        ]

        widgets = {

            "encounter_type": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),

            "chief_complaint": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": (
                        "Enter patient's chief complaint..."
                    ),
                }
            ),

            "history_of_present_illness": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": (
                        "Describe the history of the present illness..."
                    ),
                }
            ),

            "clinical_examination": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": (
                        "Record clinical examination findings..."
                    ),
                }
            ),

            "assessment": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": (
                        "Enter the clinical assessment..."
                    ),
                }
            ),

            "treatment_plan": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": (
                        "Enter treatment plan..."
                    ),
                }
            ),

            "clinical_notes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": (
                        "Additional clinical notes..."
                    ),
                }
            ),

            "follow_up_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),

            "follow_up_instructions": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": (
                        "Enter follow-up instructions..."
                    ),
                }
            ),
        }


# =========================================================
# VITAL SIGNS FORM
# =========================================================

class VitalSignsForm(forms.ModelForm):

    class Meta:

        model = VitalSigns

        fields = [
            "temperature",
            "systolic_bp",
            "diastolic_bp",
            "pulse_rate",
            "respiratory_rate",
            "oxygen_saturation",
            "weight_kg",
            "height_cm",
        ]

        widgets = {

            "temperature": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.1",
                    "placeholder": "°C",
                }
            ),

            "systolic_bp": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "mmHg",
                }
            ),

            "diastolic_bp": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "mmHg",
                }
            ),

            "pulse_rate": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "bpm",
                }
            ),

            "respiratory_rate": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "breaths/min",
                }
            ),

            "oxygen_saturation": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.1",
                    "placeholder": "%",
                }
            ),

            "weight_kg": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.1",
                    "placeholder": "kg",
                }
            ),

            "height_cm": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.1",
                    "placeholder": "cm",
                }
            ),
        }


# =========================================================
# DIAGNOSIS FORM
# =========================================================

class DiagnosisForm(forms.ModelForm):

    class Meta:

        model = Diagnosis

        fields = [
            "diagnosis_code",
            "diagnosis_name",
            "is_primary",
            "notes",
        ]

        widgets = {

            "diagnosis_code": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Optional diagnosis code",
                }
            ),

            "diagnosis_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Diagnosis name",
                }
            ),

            "is_primary": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),

            "notes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Diagnosis notes...",
                }
            ),
        }


# =========================================================
# LABORATORY REQUEST FORM
# =========================================================

class LabRequestForm(forms.Form):

    test = forms.ModelChoiceField(
        queryset=LabTest.objects.none(),
        empty_label="Select laboratory test",
        widget=forms.Select(
            attrs={
                "class": "form-select",
            }
        ),
        label="Laboratory Test",
    )

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.fields["test"].queryset = (
            LabTest.objects
            .all()
            .order_by("category", "name")
        )

        self.fields["test"].label_from_instance = (
            lambda test:
            f"{test.name} — "
            f"{test.category} — "
            f"UGX {test.price:,.0f}"
        )