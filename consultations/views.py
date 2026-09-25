from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)

from patients.models import Patient

from laboratory.models import (
    LabRequest,
    LabResult,
)

from billing.services import add_lab_charge

from .forms import (
    ClinicalEncounterForm,
    VitalSignsForm,
    DiagnosisForm,
    LabRequestForm,
)

from .models import (
    ClinicalEncounter,
    VitalSigns,
    Diagnosis,
)


# =========================================================
# DOCTOR WORKSPACE
# =========================================================

@login_required
def consultation_dashboard(request):

    encounters = (
        ClinicalEncounter.objects
        .select_related(
            "patient",
            "doctor",
        )
        .order_by("-encounter_date")
    )

    if not request.user.is_staff:

        encounters = encounters.filter(
            doctor=request.user
        )

    total_encounters = encounters.count()

    open_encounters = encounters.filter(
        status__in=[
            ClinicalEncounter.Status.OPEN,
            ClinicalEncounter.Status.IN_PROGRESS,
        ]
    ).count()

    completed_encounters = encounters.filter(
        status=ClinicalEncounter.Status.COMPLETED
    ).count()

    context = {
        "encounters": encounters[:50],
        "total_encounters": total_encounters,
        "open_encounters": open_encounters,
        "completed_encounters": completed_encounters,
    }

    return render(
        request,
        "consultations/dashboard.html",
        context,
    )


# =========================================================
# CREATE PATIENT CONSULTATION
# =========================================================

@login_required
@transaction.atomic
def patient_consultation(request, patient_id):

    patient = get_object_or_404(
        Patient,
        id=patient_id,
    )

    active_encounter = (
        ClinicalEncounter.objects
        .filter(
            patient=patient,
            status__in=[
                ClinicalEncounter.Status.OPEN,
                ClinicalEncounter.Status.IN_PROGRESS,
            ],
        )
        .order_by("-encounter_date")
        .first()
    )

    if request.method == "POST":

        encounter_form = ClinicalEncounterForm(
            request.POST
        )

        if encounter_form.is_valid():

            existing_encounter = (
                ClinicalEncounter.objects
                .filter(
                    patient=patient,
                    status__in=[
                        ClinicalEncounter.Status.OPEN,
                        ClinicalEncounter.Status.IN_PROGRESS,
                    ],
                )
                .order_by("-encounter_date")
                .first()
            )

            if existing_encounter:

                messages.warning(
                    request,
                    (
                        "This patient already has an active "
                        "clinical encounter."
                    ),
                )

                return redirect(
                    "consultations:encounter_detail",
                    encounter_id=existing_encounter.id,
                )

            encounter = encounter_form.save(
                commit=False
            )

            encounter.patient = patient
            encounter.doctor = request.user
            encounter.status = (
                ClinicalEncounter.Status.IN_PROGRESS
            )

            encounter.save()

            messages.success(
                request,
                "Clinical encounter created successfully.",
            )

            return redirect(
                "consultations:encounter_detail",
                encounter_id=encounter.id,
            )

    else:

        encounter_form = ClinicalEncounterForm()

    context = {
        "patient": patient,
        "active_encounter": active_encounter,
        "encounter_form": encounter_form,
    }

    return render(
        request,
        "consultations/patient_consultation.html",
        context,
    )


# =========================================================
# ENCOUNTER DETAIL
# =========================================================

@login_required
def encounter_detail(request, encounter_id):

    encounter = get_object_or_404(
        ClinicalEncounter.objects
        .select_related(
            "patient",
            "doctor",
        ),
        id=encounter_id,
    )

    # -----------------------------------------------------
    # SECURITY
    # -----------------------------------------------------

    if (
        not request.user.is_staff
        and encounter.doctor_id != request.user.id
    ):

        messages.error(
            request,
            "You are not authorized to access this encounter.",
        )

        return redirect(
            "consultations:consultation_dashboard"
        )

    # -----------------------------------------------------
    # VITAL SIGNS
    # -----------------------------------------------------

    vital_signs = getattr(
        encounter,
        "vital_signs",
        None,
    )

    # -----------------------------------------------------
    # DIAGNOSES
    # -----------------------------------------------------

    diagnoses = (
        encounter.diagnoses
        .all()
        .order_by(
            "-is_primary",
            "diagnosis_name",
        )
    )

    # -----------------------------------------------------
    # LABORATORY REQUESTS
    # -----------------------------------------------------

    lab_requests = (
        LabRequest.objects
        .filter(
            encounter=encounter
        )
        .select_related(
            "test",
            "requested_by",
        )
        .prefetch_related(
            "result_record"
        )
        .order_by("-requested_date")
    )

    # -----------------------------------------------------
    # BILLING
    # -----------------------------------------------------

    invoice = None

    try:

        from billing.models import Invoice

        invoice = (
            Invoice.objects
            .filter(
                patient=encounter.patient,
                encounter=encounter,
            )
            .exclude(
                status="CANCELLED"
            )
            .order_by("-invoice_date")
            .first()
        )

    except Exception:
        invoice = None

    context = {
        "encounter": encounter,
        "patient": encounter.patient,

        "vital_signs": vital_signs,
        "vital_form": VitalSignsForm(
            instance=vital_signs
        ),

        "diagnoses": diagnoses,
        "diagnosis_form": DiagnosisForm(),

        "lab_requests": lab_requests,
        "lab_request_form": LabRequestForm(),

        "invoice": invoice,
    }

    return render(
        request,
        "consultations/encounter_detail.html",
        context,
    )


# =========================================================
# SAVE VITAL SIGNS
# =========================================================

@login_required
@transaction.atomic
def save_vital_signs(request, encounter_id):

    encounter = get_object_or_404(
        ClinicalEncounter,
        id=encounter_id,
    )

    if (
        not request.user.is_staff
        and encounter.doctor_id != request.user.id
    ):

        messages.error(
            request,
            "You are not authorized to modify this encounter.",
        )

        return redirect(
            "consultations:consultation_dashboard"
        )

    if encounter.status in [
        ClinicalEncounter.Status.COMPLETED,
        ClinicalEncounter.Status.CANCELLED,
    ]:

        messages.error(
            request,
            "Vital signs cannot be modified on a closed encounter.",
        )

        return redirect(
            "consultations:encounter_detail",
            encounter_id=encounter.id,
        )

    if request.method != "POST":

        return redirect(
            "consultations:encounter_detail",
            encounter_id=encounter.id,
        )

    vital_signs = getattr(
        encounter,
        "vital_signs",
        None,
    )

    form = VitalSignsForm(
        request.POST,
        instance=vital_signs,
    )

    if form.is_valid():

        vitals = form.save(
            commit=False
        )

        vitals.encounter = encounter
        vitals.recorded_by = request.user

        vitals.save()

        messages.success(
            request,
            "Vital signs saved successfully.",
        )

    else:

        messages.error(
            request,
            "Please correct the vital signs form.",
        )

    return redirect(
        "consultations:encounter_detail",
        encounter_id=encounter.id,
    )


# =========================================================
# ADD DIAGNOSIS
# =========================================================

@login_required
@transaction.atomic
def add_diagnosis(request, encounter_id):

    encounter = get_object_or_404(
        ClinicalEncounter,
        id=encounter_id,
    )

    if (
        not request.user.is_staff
        and encounter.doctor_id != request.user.id
    ):

        messages.error(
            request,
            "You are not authorized to modify this encounter.",
        )

        return redirect(
            "consultations:consultation_dashboard"
        )

    if encounter.status in [
        ClinicalEncounter.Status.COMPLETED,
        ClinicalEncounter.Status.CANCELLED,
    ]:

        messages.error(
            request,
            "Diagnosis cannot be added to a closed encounter.",
        )

        return redirect(
            "consultations:encounter_detail",
            encounter_id=encounter.id,
        )

    if request.method == "POST":

        form = DiagnosisForm(
            request.POST
        )

        if form.is_valid():

            diagnosis = form.save(
                commit=False
            )

            diagnosis.encounter = encounter

            diagnosis.save()

            messages.success(
                request,
                "Diagnosis added successfully.",
            )

        else:

            messages.error(
                request,
                "Please correct the diagnosis form.",
            )

    return redirect(
        "consultations:encounter_detail",
        encounter_id=encounter.id,
    )


# =========================================================
# REQUEST LABORATORY TEST
# =========================================================

@login_required
@transaction.atomic
def request_lab_test(request, encounter_id):

    encounter = get_object_or_404(
        ClinicalEncounter.objects.select_related(
            "patient",
            "doctor",
        ),
        id=encounter_id,
    )

    if (
        not request.user.is_staff
        and encounter.doctor_id != request.user.id
    ):

        messages.error(
            request,
            "You are not authorized to modify this encounter.",
        )

        return redirect(
            "consultations:consultation_dashboard"
        )

    if encounter.status in [
        ClinicalEncounter.Status.COMPLETED,
        ClinicalEncounter.Status.CANCELLED,
    ]:

        messages.error(
            request,
            "Laboratory tests cannot be requested on a closed encounter.",
        )

        return redirect(
            "consultations:encounter_detail",
            encounter_id=encounter.id,
        )

    if request.method != "POST":

        return redirect(
            "consultations:encounter_detail",
            encounter_id=encounter.id,
        )

    form = LabRequestForm(
        request.POST
    )

    if not form.is_valid():

        messages.error(
            request,
            "Please select a valid laboratory test.",
        )

        return redirect(
            "consultations:encounter_detail",
            encounter_id=encounter.id,
        )

    test = form.cleaned_data["test"]

    # -----------------------------------------------------
    # PREVENT DUPLICATE ACTIVE REQUESTS
    # -----------------------------------------------------

    existing_request = (
        LabRequest.objects
        .filter(
            encounter=encounter,
            test=test,
            status__in=[
                "Pending",
                "Sample Collected",
                "Processing",
            ],
        )
        .first()
    )

    if existing_request:

        messages.warning(
            request,
            (
                f"{test.name} has already been requested "
                "for this encounter and is still active."
            ),
        )

        return redirect(
            "consultations:encounter_detail",
            encounter_id=encounter.id,
        )

    # -----------------------------------------------------
    # CREATE LAB REQUEST
    # -----------------------------------------------------

    lab_request = LabRequest.objects.create(
        patient=encounter.patient,
        encounter=encounter,
        test=test,
        requested_by=request.user,
    )

    # -----------------------------------------------------
    # CREATE BILLING CHARGE
    # -----------------------------------------------------

    try:

        add_lab_charge(
            lab_request
        )

    except ValidationError as exc:

        transaction.set_rollback(True)

        messages.error(
            request,
            str(exc),
        )

        return redirect(
            "consultations:encounter_detail",
            encounter_id=encounter.id,
        )

    except Exception:

        transaction.set_rollback(True)

        messages.error(
            request,
            (
                "The laboratory request could not be completed "
                "because the billing charge could not be created."
            ),
        )

        return redirect(
            "consultations:encounter_detail",
            encounter_id=encounter.id,
        )

    messages.success(
        request,
        (
            f"{test.name} requested successfully. "
            f"Sample number: {lab_request.sample_number}"
        ),
    )

    return redirect(
        "consultations:encounter_detail",
        encounter_id=encounter.id,
    )


# =========================================================
# COMPLETE ENCOUNTER
# =========================================================

@login_required
@transaction.atomic
def complete_encounter(request, encounter_id):

    encounter = get_object_or_404(
        ClinicalEncounter,
        id=encounter_id,
    )

    if (
        not request.user.is_staff
        and encounter.doctor_id != request.user.id
    ):

        messages.error(
            request,
            "You are not authorized to complete this encounter.",
        )

        return redirect(
            "consultations:consultation_dashboard"
        )

    if encounter.status == ClinicalEncounter.Status.COMPLETED:

        messages.info(
            request,
            "This encounter has already been completed.",
        )

        return redirect(
            "consultations:encounter_detail",
            encounter_id=encounter.id,
        )

    if encounter.status == ClinicalEncounter.Status.CANCELLED:

        messages.error(
            request,
            "A cancelled encounter cannot be completed.",
        )

        return redirect(
            "consultations:encounter_detail",
            encounter_id=encounter.id,
        )

    if request.method != "POST":

        return redirect(
            "consultations:encounter_detail",
            encounter_id=encounter.id,
        )

    # -----------------------------------------------------
    # WARN IF THERE ARE STILL ACTIVE LAB REQUESTS
    # -----------------------------------------------------

    pending_lab_count = (
        LabRequest.objects
        .filter(
            encounter=encounter,
            status__in=[
                "Pending",
                "Sample Collected",
                "Processing",
            ],
        )
        .count()
    )

    if pending_lab_count > 0:

        messages.warning(
            request,
            (
                f"There are {pending_lab_count} laboratory "
                "request(s) still in progress. The encounter "
                "will be completed, but pending results will "
                "remain available to the doctor."
            ),
        )

    encounter.status = (
        ClinicalEncounter.Status.COMPLETED
    )

    encounter.save(
        update_fields=[
            "status",
            "updated_at",
        ]
    )

    messages.success(
        request,
        "Clinical encounter completed successfully.",
    )

    return redirect(
        "consultations:consultation_dashboard"
    )

@login_required
def doctor_workspace(request):

    encounters = (
        ClinicalEncounter.objects
        .select_related("patient", "doctor")
        .filter(doctor=request.user)
        .order_by("-encounter_date")
    )

    total_encounters = encounters.count()

    open_encounters = encounters.filter(
        status__in=["OPEN", "IN_PROGRESS"]
    ).count()

    completed_encounters = encounters.filter(
        status="COMPLETED"
    ).count()

    context = {
        "encounters": encounters,
        "total_encounters": total_encounters,
        "open_encounters": open_encounters,
        "completed_encounters": completed_encounters,
    }

    return render(
        request,
        "consultations/doctor_workspace.html",
        context
    )
