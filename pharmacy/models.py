

from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from patients.models import Patient


# =========================================================
# MEDICINE
# =========================================================

class Medicine(models.Model):

    CATEGORY_CHOICES = (
        ("ANTIBIOTIC", "Antibiotic"),
        ("ANALGESIC", "Analgesic"),
        ("ANTIMALARIAL", "Antimalarial"),
        ("ANTIVIRAL", "Antiviral"),
        ("ANTIFUNGAL", "Antifungal"),
        ("ANTIHYPERTENSIVE", "Antihypertensive"),
        ("ANTIDIABETIC", "Antidiabetic"),
        ("VITAMIN", "Vitamin"),
        ("OTHER", "Other"),
    )

    DOSAGE_FORM_CHOICES = (
        ("TABLET", "Tablet"),
        ("CAPSULE", "Capsule"),
        ("SYRUP", "Syrup"),
        ("INJECTION", "Injection"),
        ("CREAM", "Cream"),
        ("OINTMENT", "Ointment"),
        ("DROPS", "Drops"),
        ("INHALER", "Inhaler"),
        ("SUSPENSION", "Suspension"),
        ("OTHER", "Other"),
    )

    STATUS_CHOICES = (
        ("ACTIVE", "Active"),
        ("INACTIVE", "Inactive"),
    )

    # Basic information
    name = models.CharField(max_length=200)
    generic_name = models.CharField(max_length=200, blank=True, null=True)
    brand_name = models.CharField(max_length=200, blank=True, null=True)

    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES
    )

    dosage_form = models.CharField(
        max_length=50,
        choices=DOSAGE_FORM_CHOICES
    )

    strength = models.CharField(max_length=100, blank=True, null=True)

    UNIT_CHOICES = (
        ("TABLET", "Tablet"),
        ("CAPSULE", "Capsule"),
        ("BOTTLE", "Bottle"),
        ("VIAL", "Vial"),
        ("AMPOULE", "Ampoule"),
        ("TUBE", "Tube"),
        ("SACHET", "Sachet"),
        ("PACK", "Pack"),
        ("PIECE", "Piece"),
        ("ML", "Millilitre (mL)"),
        ("DROP", "Drop"),
        ("PUFF", "Puff"),
        ("SUPPOSITORY", "Suppository"),
        ("OTHER", "Other"),
    )

    unit = models.CharField(
        max_length=50,
        choices=UNIT_CHOICES,
        default="OTHER",
        help_text="Select the unit used when dispensing this medicine."
    )

    # Supplier
    manufacturer = models.CharField(max_length=200, blank=True, null=True)
    supplier = models.CharField(max_length=200, blank=True, null=True)

    # Stock
    batch_number = models.CharField(max_length=100, blank=True, null=True)
    expiry_date = models.DateField(null=True, blank=True)
    quantity = models.PositiveIntegerField(default=0)
    reorder_level = models.PositiveIntegerField(default=10)

    # Pricing
    buying_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))]
    )

    selling_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))]
    )

    # Prescription / control
    prescription_required = models.BooleanField(default=False)
    controlled_substance = models.BooleanField(default=False)

    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="ACTIVE"
    )

    description = models.TextField(blank=True, null=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Helpers
    def is_expired(self):
        if not self.expiry_date:
            return False
        return self.expiry_date < timezone.now().date()

    def is_low_stock(self):
        return 0 < self.quantity <= self.reorder_level

    def is_out_of_stock(self):
        return self.quantity <= 0

    def stock_value(self):
        return self.quantity * self.buying_price

    def selling_value(self):
        return self.quantity * self.selling_price

    def __str__(self):
        if self.strength:
            return f"{self.name} {self.strength}"
        return self.name

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["category"]),
            models.Index(fields=["status"]),
            models.Index(fields=["expiry_date"]),
        ]


# =========================================================
# PRESCRIPTION
# =========================================================

class Prescription(models.Model):

    STATUS_CHOICES = (
        ("PENDING", "Pending"),
        ("PARTIALLY_DISPENSED", "Partially Dispensed"),
        ("DISPENSED", "Dispensed"),
        ("CANCELLED", "Cancelled"),
    )

    patient = models.ForeignKey(
        Patient,
        on_delete=models.PROTECT,
        related_name="prescriptions"
    )

    encounter = models.ForeignKey(
        "consultations.ClinicalEncounter",
        on_delete=models.PROTECT,
        related_name="prescriptions",
        null=True,
        blank=True
    )

    prescribed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="prescriptions_created"
    )

    diagnosis = models.TextField(blank=True)

    # Nullable to preserve the existing migration definition.
    notes = models.TextField(blank=True, null=True)

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default="PENDING"
    )

    prescribed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Prescription #{self.id} - {self.patient}"

    class Meta:
        ordering = ["-prescribed_at"]
        indexes = [
            models.Index(fields=["patient", "status"]),
            models.Index(fields=["encounter"]),
            models.Index(fields=["prescribed_at"]),
        ]


# =========================================================
# PRESCRIPTION ITEM
# =========================================================

class PrescriptionItem(models.Model):

    prescription = models.ForeignKey(
        Prescription,
        on_delete=models.CASCADE,
        related_name="items"
    )

    medicine = models.ForeignKey(
        Medicine,
        on_delete=models.PROTECT,
        related_name="prescription_items"
    )

    dosage = models.CharField(max_length=100)
    frequency = models.CharField(max_length=100)
    duration = models.CharField(max_length=100)

    quantity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)]
    )

    dispensed_quantity = models.PositiveIntegerField(default=0)

    instructions = models.TextField(blank=True, null=True)

    @property
    def remaining_quantity(self):
        return max(self.quantity - self.dispensed_quantity, 0)

    @property
    def fully_dispensed(self):
        return self.dispensed_quantity >= self.quantity

    def __str__(self):
        return f"{self.medicine} - {self.quantity}"

    class Meta:
        indexes = [
            models.Index(fields=["prescription"]),
            models.Index(fields=["medicine"]),
        ]


# =========================================================
# PHARMACY SALE
# =========================================================

class PharmacySale(models.Model):

    PAYMENT_STATUS_CHOICES = (
        ("PENDING", "Pending"),
        ("PAID", "Paid"),
        ("PARTIAL", "Partial"),
        ("CANCELLED", "Cancelled"),
    )

    PAYMENT_METHOD_CHOICES = (
        ("CASH", "Cash"),
        ("MOBILE_MONEY", "Mobile Money"),
        ("CARD", "Card"),
        ("INSURANCE", "Insurance"),
        ("BANK", "Bank"),
        ("OTHER", "Other"),
    )

    sale_number = models.CharField(
        max_length=30,
        unique=True,
        editable=False
    )

    patient = models.ForeignKey(
        Patient,
        on_delete=models.PROTECT,
        related_name="pharmacy_sales",
        null=True,
        blank=True
    )

    # Legacy field retained for compatibility.
    patient_name = models.CharField(max_length=200)

    patient_number = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    encounter = models.ForeignKey(
        "consultations.ClinicalEncounter",
        on_delete=models.PROTECT,
        related_name="pharmacy_sales",
        null=True,
        blank=True
    )

    prescription = models.ForeignKey(
        Prescription,
        on_delete=models.PROTECT,
        related_name="pharmacy_sales",
        null=True,
        blank=True
    )

    issued_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pharmacy_sales"
    )

    sale_date = models.DateTimeField(default=timezone.now)

    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00")
    )

    amount_paid = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00")
    )

    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default="PENDING"
    )

    payment_method = models.CharField(
        max_length=30,
        choices=PAYMENT_METHOD_CHOICES,
        blank=True,
        null=True
    )

    paid_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pharmacy_payments"
    )

    paid_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.sale_number:
            year = timezone.now().year

            last_sale = (
                PharmacySale.objects
                .filter(sale_number__startswith=f"PS-{year}-")
                .order_by("-id")
                .first()
            )

            next_number = 1

            if last_sale:
                try:
                    last_number = int(last_sale.sale_number.split("-")[-1])
                    next_number = last_number + 1
                except (ValueError, AttributeError):
                    next_number = 1

            self.sale_number = f"PS-{year}-{next_number:05d}"

        super().save(*args, **kwargs)

    @property
    def balance(self):
        return max(
            self.total_amount - self.amount_paid,
            Decimal("0.00")
        )

    def __str__(self):
        return self.sale_number

    class Meta:
        ordering = ["-sale_date"]
        indexes = [
            models.Index(fields=["sale_date"]),
            models.Index(fields=["patient"]),
            models.Index(fields=["encounter"]),
            models.Index(fields=["prescription"]),
            models.Index(fields=["payment_status"]),
        ]


# =========================================================
# PHARMACY SALE ITEM
# =========================================================

class PharmacySaleItem(models.Model):

    sale = models.ForeignKey(
        PharmacySale,
        on_delete=models.PROTECT,
        related_name="items"
    )

    prescription_item = models.ForeignKey(
        PrescriptionItem,
        on_delete=models.PROTECT,
        related_name="dispensed_items",
        null=True,
        blank=True
    )

    medicine = models.ForeignKey(
        Medicine,
        on_delete=models.PROTECT,
        related_name="sale_items"
    )

    quantity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)]
    )

    buying_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))]
    )

    selling_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))]
    )

    total_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00")
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        self.total_price = self.selling_price * self.quantity
        super().save(*args, **kwargs)

    @property
    def total_cost(self):
        return self.buying_price * self.quantity

    @property
    def profit(self):
        return self.total_price - self.total_cost

    def __str__(self):
        return f"{self.medicine} x {self.quantity}"

    class Meta:
        ordering = ["id"]
        indexes = [
            models.Index(fields=["sale"]),
            models.Index(fields=["medicine"]),
            models.Index(fields=["prescription_item"]),
        ]


# =========================================================
# PHARMACY AUDIT LOG
# =========================================================

class PharmacyAuditLog(models.Model):

    ACTION_CHOICES = (
        ("MEDICINE_CREATED", "Medicine Created"),
        ("MEDICINE_UPDATED", "Medicine Updated"),
        ("MEDICINE_DELETED", "Medicine Deleted"),
        ("MEDICINE_DISPENSED", "Medicine Dispensed"),
        ("PAYMENT_RECEIVED", "Payment Received"),
        ("PRESCRIPTION_CREATED", "Prescription Created"),
        ("STOCK_ADJUSTED", "Stock Adjusted"),
        ("SALE_CANCELLED", "Sale Cancelled"),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    action = models.CharField(
        max_length=50,
        choices=ACTION_CHOICES
    )

    reference = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    description = models.TextField(blank=True)

    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

