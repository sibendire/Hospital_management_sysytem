from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils import timezone


# =========================================================
# CLINICAL ENCOUNTER
# =========================================================

class ClinicalEncounter(models.Model):

    class EncounterType(models.TextChoices):
        OUTPATIENT = "OUTPATIENT", "Outpatient"
        FOLLOW_UP = "FOLLOW_UP", "Follow-up"
        EMERGENCY = "EMERGENCY", "Emergency"
        INPATIENT = "INPATIENT", "Inpatient"

    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"

    patient = models.ForeignKey(
        "patients.Patient",
        on_delete=models.PROTECT,
        related_name="clinical_encounters"
    )

    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="clinical_encounters"
    )

    encounter_number = models.CharField(
        max_length=30,
        unique=True,
        editable=False
    )

    encounter_type = models.CharField(
        max_length=20,
        choices=EncounterType.choices,
        default=EncounterType.OUTPATIENT
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.OPEN
    )

    encounter_date = models.DateTimeField(
        default=timezone.now
    )

    chief_complaint = models.TextField(
        blank=True
    )

    history_of_present_illness = models.TextField(
        blank=True
    )

    clinical_examination = models.TextField(
        blank=True
    )

    assessment = models.TextField(
        blank=True
    )

    treatment_plan = models.TextField(
        blank=True
    )

    clinical_notes = models.TextField(
        blank=True
    )

    follow_up_date = models.DateField(
        null=True,
        blank=True
    )

    follow_up_instructions = models.TextField(
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        db_table = "clinical_encounters"

        ordering = [
            "-encounter_date"
        ]

        indexes = [
            models.Index(
                fields=["patient"]
            ),
            models.Index(
                fields=["doctor"]
            ),
            models.Index(
                fields=["status"]
            ),
            models.Index(
                fields=["encounter_date"]
            ),
            models.Index(
                fields=["patient", "encounter_date"]
            ),
        ]

    def save(self, *args, **kwargs):

        if not self.encounter_number:

            year = timezone.now().year

            last = (
                ClinicalEncounter.objects
                .filter(
                    encounter_number__startswith=f"ENC-{year}-"
                )
                .order_by("-id")
                .first()
            )

            if last:

                try:
                    number = (
                        int(
                            last.encounter_number.split("-")[-1]
                        ) + 1
                    )

                except (ValueError, IndexError):

                    number = 1

            else:

                number = 1

            self.encounter_number = (
                f"ENC-{year}-{number:06d}"
            )

        super().save(*args, **kwargs)

    def __str__(self):

        return (
            f"{self.encounter_number} - "
            f"{self.patient.first_name} "
            f"{self.patient.last_name}"
        )


# =========================================================
# VITAL SIGNS
# =========================================================

class VitalSigns(models.Model):

    encounter = models.OneToOneField(
        ClinicalEncounter,
        on_delete=models.PROTECT,
        related_name="vital_signs"
    )

    temperature = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        null=True,
        blank=True,
        validators=[
            MinValueValidator(25),
            MaxValueValidator(45),
        ]
    )

    systolic_bp = models.PositiveIntegerField(
        null=True,
        blank=True
    )

    diastolic_bp = models.PositiveIntegerField(
        null=True,
        blank=True
    )

    pulse_rate = models.PositiveIntegerField(
        null=True,
        blank=True
    )

    respiratory_rate = models.PositiveIntegerField(
        null=True,
        blank=True
    )

    oxygen_saturation = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[
            MaxValueValidator(100)
        ]
    )

    weight_kg = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )

    height_cm = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )

    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="recorded_vital_signs"
    )

    recorded_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        db_table = "clinical_vital_signs"

        indexes = [
            models.Index(
                fields=["recorded_at"]
            ),
        ]

    def __str__(self):

        return (
            f"Vitals - "
            f"{self.encounter.encounter_number}"
        )


# =========================================================
# DIAGNOSIS
# =========================================================

class Diagnosis(models.Model):

    encounter = models.ForeignKey(
        ClinicalEncounter,
        on_delete=models.PROTECT,
        related_name="diagnoses"
    )

    diagnosis_code = models.CharField(
        max_length=20,
        blank=True
    )

    diagnosis_name = models.CharField(
        max_length=255
    )

    is_primary = models.BooleanField(
        default=False
    )

    notes = models.TextField(
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        db_table = "clinical_diagnoses"

        ordering = [
            "-is_primary",
            "diagnosis_name"
        ]

        indexes = [
            models.Index(
                fields=["encounter"]
            ),
            models.Index(
                fields=["diagnosis_code"]
            ),
        ]

    def save(self, *args, **kwargs):

        # Only one diagnosis can be primary
        # for a particular clinical encounter.
        if self.is_primary:

            Diagnosis.objects.filter(
                encounter=self.encounter,
                is_primary=True
            ).exclude(
                pk=self.pk
            ).update(
                is_primary=False
            )

        super().save(*args, **kwargs)

    def __str__(self):

        return self.diagnosis_name