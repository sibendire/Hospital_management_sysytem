from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

from .forms import PatientForm
from .models import Patient


def add_patient(request):

    if request.method == "POST":

        form = PatientForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():

            form.save()

            return redirect("patient_list")

    else:

        form = PatientForm()

    return render(
        request,
        "patients/add_patient.html",
        {
            "form": form
        }
    )


def patient_list(request):

    patients = Patient.objects.all().order_by("-id")

    return render(
        request,
        "patients/patient_list.html",
        {
            "patients": patients
        }
    )
@login_required
def dashboard(request):

    patients = Patient.objects.order_by("-created_at")

    context = {
        "patients_count": patients.count(),
        "patients": patients[:5],
    }

    return render(
        request,
        "dashboard.html",
        context
    )