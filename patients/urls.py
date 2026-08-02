from django.urls import path
from . import views

urlpatterns = [
    path("patient_list/", views.patient_list, name="patient_list"),
    path("add_patient/", views.add_patient, name="add_patient"),
]