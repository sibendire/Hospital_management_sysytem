from django.db import models
from django.contrib.auth.models import User

from patients.models import Patient


# =========================================================
# LABORATORY TEST
# =========================================================

class LabTest(models.Model):

    CATEGORY = (

        ("Hematology", "Hematology"),
        ("Chemistry", "Chemistry"),
        ("Microbiology", "Microbiology"),
        ("Parasitology", "Parasitology"),
        ("Urinalysis", "Urinalysis"),
        ("Immunology", "Immunology"),

    )

    name = models.CharField(
        max_length=150
    )

    category = models.CharField(
        max_length=50,
        choices=CATEGORY
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    description = models.TextField(
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]


# =========================================================
# LAB REQUEST
# =========================================================

class LabRequest(models.Model):

    STATUS = (

        ("Pending", "Pending"),
        ("Sample Collected", "Sample Collected"),
        ("Processing", "Processing"),
        ("Completed", "Completed"),

    )

    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name="lab_requests"
    )

    test = models.ForeignKey(
        LabTest,
        on_delete=models.PROTECT,
        related_name="lab_requests"
    )

    sample_number = models.CharField(
        max_length=50,
        unique=True
    )

    status = models.CharField(
        max_length=50,
        choices=STATUS,
        default="Pending"
    )

    requested_date = models.DateTimeField(
        auto_now_add=True
    )

    requested_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="lab_requests"
    )

    def __str__(self):
        return self.sample_number

    class Meta:
        ordering = ["-requested_date"]


# =========================================================
# LAB RESULT
# =========================================================

class LabResult(models.Model):

    lab_request = models.OneToOneField(
        LabRequest,
        on_delete=models.CASCADE,
        related_name="result_record"
    )

    result = models.TextField()

    interpretation = models.TextField(
        blank=True
    )

    technician = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="lab_results"
    )

    result_date = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.lab_request.sample_number

    class Meta:
        ordering = ["-result_date"]