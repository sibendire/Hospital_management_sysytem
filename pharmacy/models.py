from django.db import models

# Create your models here.
class Medicine(models.Model):
    CATEGORY = (
        ('Tablet', 'Tablet'),
        ('Capsule', 'Capsule'),
        ('Injection', 'Injection'),
        ('Syrup', 'Syrup'),
        ('Cream', 'Cream'),
        ('Drops', 'Drops'),
        ('Medical Supply', 'Medical Supply'),
    )
    name = models.CharField(max_length=200)
    batch_number = models.CharField(max_length=100,unique=True)
    category = models.CharField(max_length=50,
                                choices= CATEGORY)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10,decimal_places=2)
    expiry_date = models.DateField()
    manufacturer_date = models.CharField(
        max_length=150
    )
    descriptions = models.TextField(blank=True)

def __str__(self):
        return self.name
