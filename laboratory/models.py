from django.db import models
from patients.models import Patient



class LabTest(models.Model):

    CATEGORY = (

        ('Hematology','Hematology'),
        ('Chemistry','Chemistry'),
        ('Microbiology','Microbiology'),
        ('Parasitology','Parasitology'),
        ('Urinalysis','Urinalysis'),
        ('Immunology','Immunology'),

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


    created_at=models.DateTimeField(
        auto_now_add=True
    )


    def __str__(self):

        return self.name






class LabRequest(models.Model):


    STATUS = (

        ('Pending','Pending'),

        ('Sample Collected','Sample Collected'),

        ('Processing','Processing'),

        ('Completed','Completed'),


    )



    patient=models.ForeignKey(

        Patient,

        on_delete=models.CASCADE

    )


    test=models.ForeignKey(

        LabTest,

        on_delete=models.CASCADE

    )


    sample_number=models.CharField(

        max_length=50,

        unique=True

    )


    status=models.CharField(

        max_length=50,

        choices=STATUS,

        default="Pending"

    )


    requested_date=models.DateTimeField(

        auto_now_add=True

    )


    requested_by=models.CharField(

        max_length=100,

        blank=True

    )



    def __str__(self):

        return self.sample_number








class LabResult(models.Model):


    lab_request=models.OneToOneField(

        LabRequest,

        on_delete=models.CASCADE

    )


    result=models.TextField()


    interpretation=models.TextField(

        blank=True

    )


    technician=models.CharField(

        max_length=100

    )


    result_date=models.DateTimeField(

        auto_now_add=True

    )


    def __str__(self):

        return self.lab_request.sample_number