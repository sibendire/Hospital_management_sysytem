from django.urls import path

from . import views


app_name = "consultations"


urlpatterns = [

    # -----------------------------------------------------
    # DOCTOR WORKSPACE
    # -----------------------------------------------------

    path(
        "",
        views.consultation_dashboard,
        name="consultation_dashboard",
    ),


    # -----------------------------------------------------
    # CREATE CONSULTATION
    # -----------------------------------------------------

    path(
        "patient/<int:patient_id>/",
        views.patient_consultation,
        name="patient_consultation",
    ),

     path(
        "doctor/",
        views.doctor_workspace,
        name="doctor_workspace"
    ),


    # -----------------------------------------------------
    # ENCOUNTER DETAIL
    # -----------------------------------------------------

    path(
        "encounter/<int:encounter_id>/",
        views.encounter_detail,
        name="encounter_detail",
    ),


    # -----------------------------------------------------
    # VITAL SIGNS
    # -----------------------------------------------------

    path(
        "encounter/<int:encounter_id>/vitals/",
        views.save_vital_signs,
        name="save_vital_signs",
    ),


    # -----------------------------------------------------
    # DIAGNOSIS
    # -----------------------------------------------------

    path(
        "encounter/<int:encounter_id>/diagnosis/",
        views.add_diagnosis,
        name="add_diagnosis",
    ),


    # -----------------------------------------------------
    # LABORATORY
    # -----------------------------------------------------

    path(
        "encounter/<int:encounter_id>/lab-request/",
        views.request_lab_test,
        name="request_lab_test",
    ),


    # -----------------------------------------------------
    # COMPLETE ENCOUNTER
    # -----------------------------------------------------

    path(
        "encounter/<int:encounter_id>/complete/",
        views.complete_encounter,
        name="complete_encounter",
    ),
]