from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)
from django.utils import timezone

from patients.models import Patient

from laboratory.models import (
    LabRequest,
    LabResult,
)

from pharmacy.models import (
    Prescription,
    PharmacySale,
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
# DOCTOR WORKSPACE / CONSULTATION DASHBOARD
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

    # -----------------------------------------------------
    # DOCTORS SEE THEIR OWN ENCOUNTERS
    # STAFF CAN SEE ALL ENCOUNTERS
    # -----------------------------------------------------

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
# CREATE PATIENT CONSULTATION / ENCOUNTER
# =========================================================

@login_required
@transaction.atomic
def patient_consultation(request, patient_id):

    patient = get_object_or_404(
        Patient,
        id=patient_id,
    )

    # -----------------------------------------------------
    # CHECK FOR EXISTING ACTIVE ENCOUNTER
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # CREATE NEW ENCOUNTER
    # -----------------------------------------------------

    if request.method == "POST":

        encounter_form = ClinicalEncounterForm(
            request.POST
        )

        if encounter_form.is_valid():

            # Re-check inside the transaction in case another
            # active encounter was created before this request.
            existing_encounter = (
                ClinicalEncounter.objects
                .select_for_update()
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

    # =====================================================
    # LABORATORY REVIEW STATUS
    # =====================================================

    completed_lab_requests = lab_requests.filter(
        status="Completed"
    )

    # A completed request is still pending if:
    #
    # 1. It has no result yet, OR
    # 2. Its result has not been reviewed by the doctor.
    #
    # This prevents one reviewed result from unlocking
    # prescription while another completed result is still
    # awaiting review.

    lab_results_pending_review = (
        completed_lab_requests.filter(
            result_record__isnull=True
        ).exists()
        or completed_lab_requests.filter(
            result_record__reviewed_at__isnull=True
        ).exists()
    )

    # Prescription becomes available only when:
    #
    # - At least one laboratory request has been completed
    # - None of the completed requests is waiting for review
    #
    lab_results_reviewed = (
        completed_lab_requests.exists()
        and not lab_results_pending_review
    )

    # -----------------------------------------------------
    # PRESCRIPTIONS
    # -----------------------------------------------------

    prescriptions = (
        Prescription.objects
        .filter(
            encounter=encounter
        )
        .select_related(
            "patient",
            "prescribed_by",
        )
        .prefetch_related(
            "items__medicine",
        )
        .order_by("-prescribed_at")
    )

    # -----------------------------------------------------
    # PHARMACY SALES / DISPENSING
    # -----------------------------------------------------

    pharmacy_sales = (
        PharmacySale.objects
        .filter(
            encounter=encounter
        )
        .select_related(
            "patient",
            "prescription",
            "issued_by",
        )
        .prefetch_related(
            "items__medicine",
            "items__prescription_item",
        )
        .order_by("-sale_date")
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
            .prefetch_related(
                "items",
            )
            .order_by("-invoice_date")
            .first()
        )

    except Exception:
        invoice = None

    # -----------------------------------------------------
    # CONTEXT
    # -----------------------------------------------------

    context = {
        "encounter": encounter,
        "patient": encounter.patient,

        # -------------------------------------------------
        # VITAL SIGNS
        # -------------------------------------------------

        "vital_signs": vital_signs,

        "vital_form": VitalSignsForm(
            instance=vital_signs
        ),

        # -------------------------------------------------
        # DIAGNOSES
        # -------------------------------------------------

        "diagnoses": diagnoses,

        "diagnosis_form": DiagnosisForm(),

        # -------------------------------------------------
        # LABORATORY
        # -------------------------------------------------

        "lab_requests": lab_requests,

        "lab_request_form": LabRequestForm(),

        "lab_results_reviewed": lab_results_reviewed,

        "lab_results_pending_review": (
            lab_results_pending_review
        ),

        # -------------------------------------------------
        # PHARMACY
        # -------------------------------------------------

        "prescriptions": prescriptions,

        "pharmacy_sales": pharmacy_sales,

        # -------------------------------------------------
        # BILLING
        # -------------------------------------------------

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

    # -----------------------------------------------------
    # SECURITY
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # CLOSED ENCOUNTER CHECK
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # POST ONLY
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # SECURITY
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # CLOSED ENCOUNTER CHECK
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # POST ONLY
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # SECURITY
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # CLOSED ENCOUNTER CHECK
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # POST ONLY
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # SECURITY
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # ALREADY COMPLETED
    # -----------------------------------------------------

    if encounter.status == ClinicalEncounter.Status.COMPLETED:

        messages.info(
            request,
            "This encounter has already been completed.",
        )

        return redirect(
            "consultations:encounter_detail",
            encounter_id=encounter.id,
        )

    # -----------------------------------------------------
    # CANCELLED
    # -----------------------------------------------------

    if encounter.status == ClinicalEncounter.Status.CANCELLED:

        messages.error(
            request,
            "A cancelled encounter cannot be completed.",
        )

        return redirect(
            "consultations:encounter_detail",
            encounter_id=encounter.id,
        )

    # -----------------------------------------------------
    # POST ONLY
    # -----------------------------------------------------

    if request.method != "POST":

        return redirect(
            "consultations:encounter_detail",
            encounter_id=encounter.id,
        )

    # -----------------------------------------------------
    # CHECK ACTIVE LAB REQUESTS
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

    # -----------------------------------------------------
    # COMPLETE ENCOUNTER
    # -----------------------------------------------------

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


# =========================================================
# DOCTOR WORKSPACE
# =========================================================

@login_required
def doctor_workspace(request):

    encounters = (
        ClinicalEncounter.objects
        .select_related(
            "patient",
            "doctor",
        )
        .filter(
            doctor=request.user
        )
        .order_by("-encounter_date")
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
        "encounters": encounters,
        "total_encounters": total_encounters,
        "open_encounters": open_encounters,
        "completed_encounters": completed_encounters,
    }

    return render(
        request,
        "consultations/doctor_workspace.html",
        context,
    )


# =========================================================
# REVIEW LABORATORY RESULT
# =========================================================

@login_required
@transaction.atomic
def review_lab_result(
    request,
    encounter_id,
    result_id,
):

    # -----------------------------------------------------
    # POST ONLY
    # -----------------------------------------------------

    if request.method != "POST":

        return redirect(
            "consultations:consultation_dashboard"
        )

    # -----------------------------------------------------
    # GET LAB RESULT
    # -----------------------------------------------------

    lab_result = get_object_or_404(
        LabResult.objects.select_related(
            "lab_request",
            "lab_request__patient",
            "lab_request__encounter",
            "lab_request__test",
        ),
        id=result_id,
    )

    lab_request = lab_result.lab_request
    encounter = lab_request.encounter

    # -----------------------------------------------------
    # ENCOUNTER MUST EXIST
    # -----------------------------------------------------

    if encounter is None:

        messages.error(
            request,
            (
                "This laboratory result is not linked "
                "to a clinical encounter."
            ),
        )

        return redirect(
            "laboratory:lab_requests"
        )

    # -----------------------------------------------------
    # VERIFY URL ENCOUNTER MATCHES RESULT ENCOUNTER
    # -----------------------------------------------------

    if encounter.id != encounter_id:

        messages.error(
            request,
            (
                "This laboratory result does not belong "
                "to the selected encounter."
            ),
        )

        return redirect(
            "consultations:consultation_dashboard"
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
            (
                "You are not authorized to review "
                "this laboratory result."
            ),
        )

        return redirect(
            "consultations:consultation_dashboard"
        )

    # -----------------------------------------------------
    # LABORATORY MUST BE COMPLETED
    # -----------------------------------------------------

    if lab_request.status != "Completed":

        messages.error(
            request,
            "This laboratory result is not yet completed.",
        )

        return redirect(
            "consultations:encounter_detail",
            encounter_id=encounter.id,
        )

    # -----------------------------------------------------
    # PREVENT DUPLICATE REVIEW
    # -----------------------------------------------------

    if lab_result.reviewed_at:

        messages.info(
            request,
            "This laboratory result has already been reviewed.",
        )

        return redirect(
            "consultations:encounter_detail",
            encounter_id=encounter.id,
        )

    # -----------------------------------------------------
    # RECORD DOCTOR REVIEW
    # -----------------------------------------------------

    lab_result.reviewed_by = request.user
    lab_result.reviewed_at = timezone.now()

    lab_result.save(
        update_fields=[
            "reviewed_by",
            "reviewed_at",
        ]
    )

    messages.success(
        request,
        (
            f"Laboratory result for "
            f"{lab_request.sample_number} "
            "has been reviewed successfully."
        ),
    )

    return redirect(
        "consultations:encounter_detail",
        encounter_id=encounter.id,
    )