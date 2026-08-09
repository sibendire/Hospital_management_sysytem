
from django import forms
from .models import Medicine

class MedicineForm(forms.ModelForm):
    class Meta:
        model = Medicine
        fields = "__all__"
        widgets = {
            "expiry_date": forms.DateInput(
                attrs={"type":"Date",
                       "Class":"form-control"}
            ),

             "name": forms.TextInput(
                attrs={
                    "class": "form-control"
                }
            ),

            "batch_number": forms.TextInput(
                attrs={
                    "class": "form-control"
                }
            ),

            "category": forms.Select(
                attrs={
                    "class": "form-select"
                }
            ),

            "quantity": forms.NumberInput(
                attrs={
                    "class": "form-control"
                }
            ),

            "unit_price": forms.NumberInput(
                attrs={
                    "class": "form-control"
                }
            ),

            "manufacturer": forms.TextInput(
                attrs={
                    "class": "form-control"
                }
            ),

            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3
                }
            ),


        }