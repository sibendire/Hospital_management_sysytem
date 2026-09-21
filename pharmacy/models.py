from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal
from django.utils import timezone



# =========================================================
# MEDICINE
# =========================================================

class Medicine(models.Model):

    CATEGORY_CHOICES = [
        ("ANTIBIOTIC", "Antibiotic"),
        ("ANALGESIC", "Analgesic"),
        ("ANTIMALARIAL", "Antimalarial"),
        ("ANTIHISTAMINE", "Antihistamine"),
        ("ANTACID", "Antacid"),
        ("ANTIVIRAL", "Antiviral"),
        ("ANTIFUNGAL", "Antifungal"),
        ("CARDIOVASCULAR", "Cardiovascular"),
        ("DIABETES", "Diabetes"),
        ("VITAMIN", "Vitamin / Supplement"),
        ("OTHER", "Other"),
    ]

    DOSAGE_FORM_CHOICES = [
        ("TABLET", "Tablet"),
        ("CAPSULE", "Capsule"),
        ("SYRUP", "Syrup"),
        ("INJECTION", "Injection"),
        ("CREAM", "Cream"),
        ("OINTMENT", "Ointment"),
        ("DROPS", "Drops"),
        ("INHALER", "Inhaler"),
        ("SUPPOSITORY", "Suppository"),
        ("SUSPENSION", "Suspension"),
        ("SOLUTION", "Solution"),
        ("OTHER", "Other"),
    ]

    UNIT_CHOICES = [
        ("TABLET", "Tablet"),
        ("CAPSULE", "Capsule"),
        ("BOTTLE", "Bottle"),
        ("VIAL", "Vial"),
        ("AMPOULE", "Ampoule"),
        ("TUBE", "Tube"),
        ("PACK", "Pack"),
        ("BOX", "Box"),
        ("PIECE", "Piece"),
    ]

    STATUS_CHOICES = [
        ("ACTIVE", "Active"),
        ("INACTIVE", "Inactive"),
        ("DISCONTINUED", "Discontinued"),
    ]

    PRESCRIPTION_CHOICES = [
        ("YES", "Prescription Required"),
        ("NO", "Prescription Not Required"),
    ]

    name = models.CharField(max_length=200)

    generic_name = models.CharField(
        max_length=200,
        blank=True,
        null=True
    )

    brand_name = models.CharField(
        max_length=200,
        blank=True,
        null=True
    )

    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES
    )

    dosage_form = models.CharField(
        max_length=50,
        choices=DOSAGE_FORM_CHOICES
    )

    strength = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    unit = models.CharField(
        max_length=30,
        choices=UNIT_CHOICES
    )

    manufacturer = models.CharField(
        max_length=200,
        blank=True,
        null=True
    )

    supplier = models.CharField(
        max_length=200,
        blank=True,
        null=True
    )

    batch_number = models.CharField(
        max_length=100
    )

    expiry_date = models.DateField()

    quantity = models.PositiveIntegerField(
        default=0
    )

    reorder_level = models.PositiveIntegerField(
        default=20
    )

    # SELLING PRICE
    buying_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal("0.00"))
        ]
    )

    # PURCHASE / COST PRICE
    selling_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[
            MinValueValidator(Decimal("0.00"))
        ]
    )

    prescription_required = models.CharField(
        max_length=3,
        choices=PRESCRIPTION_CHOICES,
        default="NO"
    )

    # CONTROLLED MEDICINE
    controlled_substance = models.BooleanField(
        default=False
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="ACTIVE"
    )

    description = models.TextField(
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def is_expired(self):
        return self.expiry_date < timezone.now().date()

    def is_low_stock(self):
        return (
            self.quantity > 0
            and self.quantity <= self.reorder_level
        )

    def is_out_of_stock(self):
        return self.quantity <= 0

    def stock_value(self):
        return self.quantity * self.cost_price

    def selling_value(self):
        return self.quantity * self.unit_price

    def __str__(self):
        return f"{self.name} - {self.batch_number}"

    class Meta:
        ordering = ["name"]

        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["batch_number"]),
            models.Index(fields=["expiry_date"]),
            models.Index(fields=["status"]),
            models.Index(fields=["category"]),
            models.Index(fields=["controlled_substance"]),
        ]


# =========================================================
# PHARMACY SALE / DISPENSING BILL
# =========================================================
# =========================================================
# PHARMACY SALE
# =========================================================

class PharmacySale(models.Model):

    PAYMENT_STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("PAID", "Paid"),
        ("PARTIAL", "Partially Paid"),
        ("CANCELLED", "Cancelled"),
    ]

    PAYMENT_METHOD_CHOICES = [
        ("CASH", "Cash"),
        ("MOBILE_MONEY", "Mobile Money"),
        ("CARD", "Card"),
        ("INSURANCE", "Insurance"),
        ("BANK", "Bank"),
        ("OTHER", "Other"),
    ]

    sale_number = models.CharField(
        max_length=30,
        unique=True,
        editable=False
    )

    patient_name = models.CharField(
        max_length=200
    )

    patient_number = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    issued_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pharmacy_sales"
    )

    sale_date = models.DateTimeField(
        auto_now_add=True
    )

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
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pharmacy_payments_received"
    )

    paid_at = models.DateTimeField(
        null=True,
        blank=True
    )

    notes = models.TextField(
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def save(self, *args, **kwargs):

        if not self.sale_number:

            today = timezone.now().strftime("%Y%m%d")

            last_sale = (
                PharmacySale.objects
                .filter(
                    sale_number__startswith=f"PS-{today}"
                )
                .order_by("-id")
                .first()
            )

            if last_sale:

                try:
                    last_number = int(
                        last_sale.sale_number.split("-")[-1]
                    )
                except (ValueError, IndexError):
                    last_number = 0

            else:
                last_number = 0

            self.sale_number = (
                f"PS-{today}-{last_number + 1:05d}"
            )

        super().save(*args, **kwargs)

    @property
    def balance(self):
        return self.total_amount - self.amount_paid

    def __str__(self):
        return self.sale_number

    class Meta:

        ordering = ["-sale_date"]

        indexes = [
            models.Index(fields=["sale_date"]),
            models.Index(fields=["patient_number"]),
            models.Index(fields=["payment_status"]),
            models.Index(fields=["payment_method"]),
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

    medicine = models.ForeignKey(
        Medicine,
        on_delete=models.PROTECT,
        related_name="sale_items"
    )

    quantity = models.PositiveIntegerField(
        validators=[
            MinValueValidator(1)
        ]
    )

    buying_price = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    selling_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00")
    )

    total_price = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def save(self, *args, **kwargs):

        self.total_price = (
            self.buying_price * self.quantity
        )

        super().save(*args, **kwargs)

    @property
    def total_cost(self):
        return self.selling_price * self.quantity

    @property
    def profit(self):
        return self.total_price - self.total_cost

    def __str__(self):
        return f"{self.medicine.name} x {self.quantity}"

    class Meta:
        ordering = ["id"]

        # =========================================================
# PHARMACY AUDIT LOG
# =========================================================

class PharmacyAuditLog(models.Model):

    ACTION_CHOICES = [
        ("MEDICINE_CREATED", "Medicine Created"),
        ("MEDICINE_UPDATED", "Medicine Updated"),
        ("MEDICINE_DELETED", "Medicine Deleted"),
        ("MEDICINE_DISPENSED", "Medicine Dispensed"),
        ("PAYMENT_RECEIVED", "Payment Received"),
        ("PRESCRIPTION_CREATED", "Prescription Created"),
        ("STOCK_ADJUSTED", "Stock Adjusted"),
        ("SALE_CANCELLED", "Sale Cancelled"),
    ]

    user = models.ForeignKey(
        User,
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

    description = models.TextField()

    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ["-created_at"]

        indexes = [
            models.Index(fields=["action"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["reference"]),
        ]

    def __str__(self):
        return f"{self.action} - {self.reference}"

# =========================================================
# PRESCRIPTION
# =========================================================

class Prescription(models.Model):

    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("PARTIALLY_DISPENSED", "Partially Dispensed"),
        ("DISPENSED", "Dispensed"),
        ("CANCELLED", "Cancelled"),
    ]

    patient = models.ForeignKey(
        "patients.Patient",
        on_delete=models.CASCADE,
        related_name="prescriptions"
    )

    prescribed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="prescriptions_created"
    )

    diagnosis = models.TextField()

    notes = models.TextField(
        blank=True,
        null=True
    )

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default="PENDING"
    )

    prescribed_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"Prescription #{self.id} - {self.patient}"

    class Meta:
        ordering = ["-prescribed_at"]


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

    dosage = models.CharField(
        max_length=100
    )

    frequency = models.CharField(
        max_length=100
    )

    duration = models.CharField(
        max_length=100
    )

    quantity = models.PositiveIntegerField(
        validators=[
            MinValueValidator(1)
        ]
    )

    instructions = models.TextField(
        blank=True,
        null=True
    )

    def __str__(self):
        return f"{self.medicine.name} - {self.quantity}"

    class Meta:
        ordering = ["id"]


 