from django.contrib import admin
from .models import Medicine

# Register your models here.
@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):

    list_display = (

        "name",

        "batch_number",

        "category",

        "quantity",

        "unit_price",

        "expiry_date",

    )

    search_fields = (

        "name",

        "batch_number",

    )

    list_filter = (

        "category",

    )