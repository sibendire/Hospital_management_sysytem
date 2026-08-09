from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from .models import Medicine
from .forms import MedicineForm


# =========================================================
# PHARMACY DASHBOARD
# =========================================================

def pharmacy_dashboard(request):

    today = timezone.now().date()

    context = {

        # Total medicines registered
        "medicine_count": Medicine.objects.count(),

        # Medicines with 20 or fewer units
        "low_stock": Medicine.objects.filter(
            quantity__lte=20
        ).count(),

        # Medicines already expired
        "expired": Medicine.objects.filter(
            expiry_date__lt=today
        ).count(),

        # Medicines currently in stock
        "available_stock": Medicine.objects.filter(
            quantity__gt=0
        ).count(),

    }

    return render(
        request,
        "pharmacy/dashboard.html",
        context
    )


# =========================================================
# MEDICINE LIST
# =========================================================

def medicine_list(request):

    medicines = Medicine.objects.all().order_by("name")

    return render(
        request,
        "pharmacy/medicine_list.html",
        {
            "medicines": medicines
        }
    )


# =========================================================
# ADD MEDICINE
# =========================================================

def add_medicine(request):

    if request.method == "POST":

        form = MedicineForm(request.POST)

        if form.is_valid():

            form.save()

            return redirect("medicine_list")

    else:

        form = MedicineForm()

    return render(
        request,
        "pharmacy/medicine_form.html",
        {
            "form": form
        }
    )


# =========================================================
# EDIT MEDICINE
# =========================================================

def edit_medicine(request, id):

    medicine = get_object_or_404(
        Medicine,
        id=id
    )

    if request.method == "POST":

        form = MedicineForm(
            request.POST,
            instance=medicine
        )

        if form.is_valid():

            form.save()

            return redirect("medicine_list")

    else:

        form = MedicineForm(
            instance=medicine
        )

    return render(
        request,
        "pharmacy/medicine_form.html",
        {
            "form": form,
            "medicine": medicine
        }
    )


# =========================================================
# DELETE MEDICINE
# =========================================================

def delete_medicine(request, id):

    medicine = get_object_or_404(
        Medicine,
        id=id
    )

    if request.method == "POST":

        medicine.delete()

        return redirect("medicine_list")

    return render(
        request,
        "pharmacy/medicine_confirm_delete.html",
        {
            "medicine": medicine
        }
    )