from django.db import models
from django.core.validators import RegexValidator


class Patient(models.Model):

    GENDER_CHOICES = (
        ("Male", "Male"),
        ("Female", "Female"),
        ("Other", "Other"),
    )

    BLOOD_GROUP_CHOICES = (
        ("A+", "A+"),
        ("A-", "A-"),
        ("B+", "B+"),
        ("B-", "B-"),
        ("AB+", "AB+"),
        ("AB-", "AB-"),
        ("O+", "O+"),
        ("O-", "O-"),
    )

    first_name = models.CharField(max_length=100)

    last_name = models.CharField(max_length=100)

    gender = models.CharField(
        max_length=10,
        choices=GENDER_CHOICES
    )

    date_of_birth = models.DateField()

    patient_number = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        editable=False
    )

    national_id = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )

    phone = models.CharField(
        max_length=15,
        validators=[
            RegexValidator(
                regex=r'^\+?\d{9,15}$',
                message="Enter a valid phone number."
            )
        ]
    )

    email = models.EmailField(
        blank=True,
        null=True
    )

    address = models.TextField()

    blood_group = models.CharField(
        max_length=3,
        choices=BLOOD_GROUP_CHOICES,
        blank=True,
        null=True
    )

    photo = models.ImageField(
        upload_to="patients/",
        blank=True,
        null=True
    )

    next_of_kin = models.CharField(
        max_length=100
    )

    next_of_kin_phone = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):

        if not self.patient_number:
            last_patient = (
                Patient.objects
                .filter(patient_number__startswith="PAT-")
                .order_by("-id")
                .first()
            )

            if last_patient:
                try:
                    last_number = int(
                        last_patient.patient_number.replace("PAT-", "")
                    )
                    next_number = last_number + 1
                except ValueError:
                    next_number = 1
            else:
                next_number = 1

            self.patient_number = f"PAT-{next_number:06d}"

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.patient_number} - {self.first_name} {self.last_name}"