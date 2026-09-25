from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from patients.models import Patient


# =========================================================
# INVOICE
# =========================================================

class Invoice(models.Model):

    STATUS_CHOICES = (
        ("UNPAID", "Unpaid"),
        ("PARTIAL", "Partially Paid"),
        ("PAID", "Paid"),
        ("CANCELLED", "Cancelled"),
    )

    PAYMENT_STATUS_CHOICES = (
        ("UNPAID", "Unpaid"),
        ("PARTIAL", "Partially Paid"),
        ("PAID", "Paid"),
    )

    # =====================================================
    # PATIENT
    # =====================================================

    patient = models.ForeignKey(
        Patient,
        on_delete=models.PROTECT,
        related_name="invoices"
    )

    # =====================================================
    # CLINICAL ENCOUNTER
    # =====================================================

    encounter = models.ForeignKey(
        "consultations.ClinicalEncounter",
        on_delete=models.PROTECT,
        related_name="invoices",
        null=True,
        blank=True
    )

    # =====================================================
    # INVOICE INFORMATION
    # =====================================================

    invoice_number = models.CharField(
        max_length=30,
        unique=True,
        blank=True
    )

    invoice_date = models.DateTimeField(
        default=timezone.now
    )

    due_date = models.DateField(
        null=True,
        blank=True
    )

    # =====================================================
    # STATUS
    # =====================================================

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="UNPAID"
    )

    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default="UNPAID"
    )

    # =====================================================
    # NOTES / AUDIT
    # =====================================================

    notes = models.TextField(
        blank=True
    )

    created_by = models.CharField(
        max_length=150,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    # =====================================================
    # INVOICE NUMBER
    # =====================================================

    def generate_invoice_number(self):

        year = timezone.now().year

        last_invoice = (
            Invoice.objects
            .filter(
                invoice_number__startswith=f"INV-{year}-"
            )
            .order_by("-id")
            .first()
        )

        if last_invoice:

            try:
                last_number = int(
                    last_invoice.invoice_number.split("-")[-1]
                )

                next_number = last_number + 1

            except (ValueError, AttributeError):

                next_number = 1

        else:

            next_number = 1

        return f"INV-{year}-{next_number:05d}"

    # =====================================================
    # SAVE
    # =====================================================

    def save(self, *args, **kwargs):

        if not self.invoice_number:

            self.invoice_number = (
                self.generate_invoice_number()
            )

        super().save(*args, **kwargs)

    # =====================================================
    # SUBTOTAL
    # =====================================================

    @property
    def subtotal(self):

        return sum(
            (
                item.total
                for item in self.items.all()
            ),
            Decimal("0.00")
        )

    # =====================================================
    # TOTAL
    # =====================================================

    @property
    def total_amount(self):

        return self.subtotal

    # =====================================================
    # AMOUNT PAID
    # =====================================================

    @property
    def amount_paid(self):

        return sum(
            (
                payment.amount
                for payment in self.payments.filter(
                    status="COMPLETED"
                )
            ),
            Decimal("0.00")
        )

    # =====================================================
    # BALANCE
    # =====================================================

    @property
    def balance(self):

        balance = (
            self.total_amount -
            self.amount_paid
        )

        return max(
            balance,
            Decimal("0.00")
        )

    # =====================================================
    # UPDATE PAYMENT STATUS
    # =====================================================

    def update_payment_status(self):

        if self.status == "CANCELLED":
            return

        total = self.total_amount
        paid = self.amount_paid

        if paid <= Decimal("0.00"):

            self.payment_status = "UNPAID"
            self.status = "UNPAID"

        elif paid < total:

            self.payment_status = "PARTIAL"
            self.status = "PARTIAL"

        else:

            self.payment_status = "PAID"
            self.status = "PAID"

        Invoice.objects.filter(
            pk=self.pk
        ).update(
            payment_status=self.payment_status,
            status=self.status
        )

    # =====================================================
    # STRING
    # =====================================================

    def __str__(self):

        return self.invoice_number

    class Meta:

        ordering = ["-invoice_date"]

        indexes = [
            models.Index(fields=["invoice_date"]),
            models.Index(fields=["status"]),
            models.Index(fields=["payment_status"]),
        ]


# =========================================================
# INVOICE ITEM
# =========================================================
#
# This is where individual hospital services are recorded.
#
# Examples:
#
# Consultation
# Laboratory
# Pharmacy
# Procedure
# Admission
# Other
#
# source_type/source_id allow us later to trace an item
# back to LabRequest, PharmacySaleItem, etc.
# =========================================================

class InvoiceItem(models.Model):

    SERVICE_TYPES = (
        ("CONSULTATION", "Consultation"),
        ("LABORATORY", "Laboratory"),
        ("PHARMACY", "Pharmacy"),
        ("PROCEDURE", "Procedure"),
        ("ADMISSION", "Admission"),
        ("OTHER", "Other"),
    )

    # =====================================================
    # INVOICE
    # =====================================================

    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name="items"
    )

    # =====================================================
    # SERVICE
    # =====================================================

    service_type = models.CharField(
        max_length=30,
        choices=SERVICE_TYPES,
        default="OTHER"
    )

    description = models.CharField(
        max_length=255
    )

    # =====================================================
    # QUANTITY / PRICE
    # =====================================================

    quantity = models.PositiveIntegerField(
        default=1,
        validators=[
            MinValueValidator(1)
        ]
    )

    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[
            MinValueValidator(
                Decimal("0.00")
            )
        ]
    )

    # =====================================================
    # SOURCE TRACEABILITY
    # =====================================================
    #
    # Example:
    #
    # source_type = "LAB_REQUEST"
    # source_id   = 15
    #
    # or:
    #
    # source_type = "PHARMACY_SALE_ITEM"
    # source_id   = 42
    #
    # These allow us to prevent duplicate billing later.
    # =====================================================

    source_type = models.CharField(
        max_length=30,
        blank=True,
        null=True
    )

    source_id = models.PositiveBigIntegerField(
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    # =====================================================
    # TOTAL
    # =====================================================

    @property
    def total(self):

        return (
            self.quantity *
            self.unit_price
        )

    def __str__(self):

        return self.description

    class Meta:

        ordering = ["id"]

        indexes = [
            models.Index(
                fields=[
                    "service_type"
                ]
            ),
            models.Index(
                fields=[
                    "source_type",
                    "source_id"
                ]
            ),
        ]


# =========================================================
# PAYMENT
# =========================================================

class Payment(models.Model):

    PAYMENT_METHODS = (
        ("CASH", "Cash"),
        ("MOBILE_MONEY", "Mobile Money"),
        ("BANK", "Bank Transfer"),
        ("CARD", "Card"),
        ("INSURANCE", "Insurance"),
    )

    PAYMENT_STATUS = (
        ("COMPLETED", "Completed"),
        ("PENDING", "Pending"),
        ("CANCELLED", "Cancelled"),
    )

    # =====================================================
    # INVOICE
    # =====================================================

    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.PROTECT,
        related_name="payments"
    )

    # =====================================================
    # RECEIPT
    # =====================================================

    receipt_number = models.CharField(
        max_length=30,
        unique=True,
        blank=True
    )

    # =====================================================
    # PAYMENT
    # =====================================================

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[
            MinValueValidator(
                Decimal("0.01")
            )
        ]
    )

    payment_method = models.CharField(
        max_length=30,
        choices=PAYMENT_METHODS
    )

    transaction_reference = models.CharField(
        max_length=100,
        blank=True
    )

    payment_date = models.DateTimeField(
        default=timezone.now
    )

    status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS,
        default="COMPLETED"
    )

    # =====================================================
    # STAFF
    # =====================================================

    received_by = models.CharField(
        max_length=150,
        blank=True
    )

    notes = models.TextField(
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    # =====================================================
    # RECEIPT NUMBER
    # =====================================================

    def generate_receipt_number(self):

        year = timezone.now().year

        last_payment = (
            Payment.objects
            .filter(
                receipt_number__startswith=f"RCT-{year}-"
            )
            .order_by("-id")
            .first()
        )

        if last_payment:

            try:

                last_number = int(
                    last_payment.receipt_number.split("-")[-1]
                )

                next_number = last_number + 1

            except (
                ValueError,
                AttributeError
            ):

                next_number = 1

        else:

            next_number = 1

        return (
            f"RCT-{year}-{next_number:05d}"
        )

    # =====================================================
    # SAVE
    # =====================================================

    def save(self, *args, **kwargs):

        if not self.receipt_number:

            self.receipt_number = (
                self.generate_receipt_number()
            )

        super().save(*args, **kwargs)

        if self.invoice_id:

            self.invoice.update_payment_status()

    # =====================================================
    # STRING
    # =====================================================

    def __str__(self):

        return self.receipt_number

    class Meta:

        ordering = ["-payment_date"]

        indexes = [
            models.Index(
                fields=["payment_date"]
            ),
            models.Index(
                fields=["status"]
            ),
            models.Index(
                fields=["payment_method"]
            ),
        ]