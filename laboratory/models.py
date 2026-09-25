from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

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
        decimal_places=2,
        default=0.00
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
# LABORATORY REQUEST
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
        on_delete=models.PROTECT,
        related_name="lab_requests"
    )

    # Links the laboratory request to the doctor's encounter.
    encounter = models.ForeignKey(
        "consultations.ClinicalEncounter",
        on_delete=models.PROTECT,
        related_name="lab_requests",
        null=True,
        blank=True
    )

    test = models.ForeignKey(
        LabTest,
        on_delete=models.PROTECT,
        related_name="lab_requests"
    )

    sample_number = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        editable=False
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

    def save(self, *args, **kwargs):

        # Generate the sample number only once.
        if not self.sample_number:

            # First save allows Django/MySQL to generate the ID.
            super().save(*args, **kwargs)

            year = timezone.now().year

            self.sample_number = (
                f"LAB-{year}-{self.pk:06d}"
            )

            # Save the generated sample number.
            super().save(
                update_fields=["sample_number"]
            )

            return

        super().save(*args, **kwargs)

    def __str__(self):
        return self.sample_number

    class Meta:
        ordering = ["-requested_date"]


# =========================================================
# LABORATORY RESULT
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