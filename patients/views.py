from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect
from .forms import PatientForm
from .models import Patient


def add_patient(request):
    if request.method == "POST":
        form = PatientForm(request.POST, request.FILES)

        if form.is_valid():
            form.save()
            return redirect("patient_list")

    else:
        form = PatientForm()

    return render(request, "patients/add_patient.html", {
        "form": form
    })


def patient_list(request):
    patients = Patient.objects.all()

    return render(request, "patients/patient_list.html", {
        "patients": patients
    })