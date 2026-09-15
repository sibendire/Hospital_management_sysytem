from django.db import models

# Create your models here.

class Ward(models.Model):

    WARD_TYPES = [
        ("GENERAL", "General"),
        ("MEDICAL", "Medical"),
        ("SURGICAL", "Surgical"),
        ("MATERNITY", "Maternity"),
        ("PEDIATRIC", "Pediatric"),
        ("ICU", "ICU"),
        ("PRIVATE", "Private"),
    ]

    name = models.CharField(max_length=150)
    ward_type = models.CharField(
        max_length=30,
        choices=WARD_TYPES,
        default="GENERAL"
    )
    description = models.TextField(blank=True)
    location = models.CharField(max_length=150, blank=True)
    active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def total_beds(self):
        return self.beds.count()

    @property
    def occupied_beds(self):
        return self.beds.filter(status="OCCUPIED").count()

    @property
    def available_beds(self):
        return self.beds.filter(status="AVAILABLE").count()


class Bed(models.Model):

    STATUS_CHOICES = [
        ("AVAILABLE", "Available"),
        ("OCCUPIED", "Occupied"),
        ("MAINTENANCE", "Maintenance"),
    ]

    ward = models.ForeignKey(
        Ward,
        on_delete=models.CASCADE,
        related_name="beds"
    )

    bed_number = models.CharField(max_length=50)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="AVAILABLE"
    )

    bed_type = models.CharField(
        max_length=50,
        default="Standard"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["bed_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["ward", "bed_number"],
                name="unique_bed_per_ward"
            )
        ]

    def __str__(self):
        return f"{self.ward.name} - {self.bed_number}"


class Admission(models.Model):

    STATUS_CHOICES = [
        ("ADMITTED", "Admitted"),
        ("DISCHARGED", "Discharged"),
        ("TRANSFERRED", "Transferred"),
    ]

    patient = models.ForeignKey(
        "patients.Patient",
        on_delete=models.PROTECT,
        related_name="admissions"
    )

    ward = models.ForeignKey(
        Ward,
        on_delete=models.PROTECT,
        related_name="admissions"
    )

    bed = models.ForeignKey(
        Bed,
        on_delete=models.PROTECT,
        related_name="admissions"
    )

    admission_date = models.DateTimeField(
        auto_now_add=True
    )

    discharge_date = models.DateTimeField(
        null=True,
        blank=True
    )

    reason = models.TextField(blank=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="ADMITTED"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.patient} - {self.ward}"