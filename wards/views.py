from django.shortcuts import render

from .models import Ward, Bed, Admission


def ward_dashboard(request):

    wards = Ward.objects.filter(
        active=True
    ).prefetch_related("beds")

    context = {
        "wards": wards,

        "total_wards": wards.count(),

        "total_beds": Bed.objects.count(),

        "occupied_beds": Bed.objects.filter(
            status="OCCUPIED"
        ).count(),

        "available_beds": Bed.objects.filter(
            status="AVAILABLE"
        ).count(),

        "active_admissions": Admission.objects.filter(
            status="ADMITTED"
        ).count(),
    }

    return render(
        request,
        "wards/ward_dashboard.html",
        context
    )