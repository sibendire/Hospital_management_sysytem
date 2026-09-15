from django.contrib import admin

from .models import Ward, Bed, Admission


@admin.register(Ward)
class WardAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "ward_type",
        "location",
        "total_beds_display",
        "occupied_beds_display",
        "available_beds_display",
        "active",
    )

    list_filter = (
        "ward_type",
        "active",
    )

    search_fields = (
        "name",
        "location",
    )

    def total_beds_display(self, obj):
        return obj.total_beds

    def occupied_beds_display(self, obj):
        return obj.occupied_beds

    def available_beds_display(self, obj):
        return obj.available_beds


@admin.register(Bed)
class BedAdmin(admin.ModelAdmin):

    list_display = (
        "bed_number",
        "ward",
        "bed_type",
        "status",
    )

    list_filter = (
        "status",
        "ward",
    )

    search_fields = (
        "bed_number",
        "ward__name",
    )


@admin.register(Admission)
class AdmissionAdmin(admin.ModelAdmin):

    list_display = (
        "patient",
        "ward",
        "bed",
        "admission_date",
        "status",
    )

    list_filter = (
        "status",
        "ward",
    )

    search_fields = (
        "patient__first_name",
        "patient__last_name",
    )