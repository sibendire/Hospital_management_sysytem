from django import forms

from .models import (
    Invoice,
    InvoiceItem,
    Payment
)


class InvoiceForm(forms.ModelForm):

    class Meta:

        model = Invoice

        fields = [
            "patient",
            "due_date",
            "notes",
        ]

        widgets = {

            "patient": forms.Select(
                attrs={
                    "class": "form-select"
                }
            ),

            "due_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date"
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


class InvoiceItemForm(forms.ModelForm):

    class Meta:

        model = InvoiceItem

        fields = [
            "service_type",
            "description",
            "quantity",
            "unit_price",
        ]

        widgets = {

            "service_type": forms.Select(
                attrs={
                    "class": "form-select"
                }
            ),

            "description": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Service description"
                }
            ),

            "quantity": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 1
                }
            ),

            "unit_price": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 0,
                    "step": "0.01"
                }
            ),
        }


class PaymentForm(forms.ModelForm):

    class Meta:

        model = Payment

        fields = [
            "amount",
            "payment_method",
            "transaction_reference",
            "notes",
        ]

        widgets = {

            "amount": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 0,
                    "step": "0.01"
                }
            ),

            "payment_method": forms.Select(
                attrs={
                    "class": "form-select"
                }
            ),

            "transaction_reference": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Transaction/reference number"
                }
            ),

            "notes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3
                }
            ),
        }

    def __init__(self, *args, **kwargs):

        invoice = kwargs.pop("invoice", None)

        super().__init__(*args, **kwargs)

        self.invoice = invoice

    def clean_amount(self):

        amount = self.cleaned_data["amount"]

        if self.invoice:

            balance = self.invoice.balance

            if amount > balance:

                raise forms.ValidationError(
                    f"Payment cannot exceed the outstanding balance "
                    f"of {balance:,.2f}."
                )

        return amount