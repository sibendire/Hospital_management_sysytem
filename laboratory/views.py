
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.db import transaction
from django.db.models.deletion import ProtectedError

from billing.services import add_lab_charge

from .forms import (
    LabRequestForm,
    LabResultForm,
    LabTestForm,
)

from .models import (
    LabRequest,
    LabResult,
    LabTest,
)


# =========================================================
# LABORATORY DASHBOARD
# =========================================================

@login_required
def laboratory_dashboard(request):

    context = {
        "tests": LabTest.objects.count(),

        "requests": LabRequest.objects.count(),

        "pending": LabRequest.objects.filter(
            status="Pending"
        ).count(),

        "completed": LabRequest.objects.filter(
            status="Completed"
        ).count(),
    }

    return render(
        request,
        "laboratory/dashboard.html",
        context
    )


# =========================================================
# LAB TEST LIST
# =========================================================

@login_required
def test_list(request):

    tests = LabTest.objects.all()

    return render(
        request,
        "laboratory/test_list.html",
        {
            "tests": tests
        }
    )


# =========================================================
# ADD LAB TEST
# =========================================================

@login_required
def add_test(request):

    if request.method == "POST":

        form = LabTestForm(request.POST)

        if form.is_valid():

            test = form.save()

            messages.success(
                request,
                f"Laboratory test '{test.name}' was added successfully."
            )

            return redirect("test_list")

    else:

        form = LabTestForm()

    return render(
        request,
        "laboratory/test_form.html",
        {
            "form": form
        }
    )


# =========================================================
# EDIT LAB TEST
# =========================================================

@login_required
def edit_test(request, id):

    test = get_object_or_404(
        LabTest,
        id=id
    )

    if request.method == "POST":

        form = LabTestForm(
            request.POST,
            instance=test
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                (
                    f"Laboratory test '{test.name}' "
                    "was updated successfully."
                )
            )

            return redirect("test_list")

    else:

        form = LabTestForm(
            instance=test
        )

    return render(
        request,
        "laboratory/test_form.html",
        {
            "form": form,
            "test": test,
            "is_edit": True,
        }
    )


# =========================================================
# DELETE LAB TEST
# =========================================================

@login_required
def delete_test(request, id):

    test = get_object_or_404(
        LabTest,
        id=id
    )

    if request.method != "POST":

        return redirect("test_list")

    test_name = test.name

    try:

        test.delete()

        messages.success(
            request,
            (
                f"Laboratory test '{test_name}' "
                "was deleted successfully."
            )
        )

    except ProtectedError:

        messages.error(
            request,
            (
                f"'{test_name}' cannot be deleted because it has "
                "already been used in one or more laboratory requests. "
                "This protects the patient's laboratory history."
            )
        )

    return redirect("test_list")


# =========================================================
# CREATE LAB REQUEST
# =========================================================

@login_required
@transaction.atomic
def create_lab_request(request):

    if request.method == "POST":

        form = LabRequestForm(request.POST)

        if form.is_valid():

            lab_request = form.save(
                commit=False
            )

            lab_request.requested_by = request.user

            lab_request.save()

            try:

                invoice, invoice_item = add_lab_charge(
                    lab_request
                )

            except Exception as exc:

                # Because this view is wrapped in transaction.atomic,
                # the LabRequest will also be rolled back if billing fails.
                messages.error(
                    request,
                    (
                        "The laboratory request could not be billed. "
                        f"Please correct the problem and try again. "
                        f"Details: {exc}"
                    )
                )

                raise

            messages.success(
                request,
                (
                    f"Laboratory request "
                    f"{lab_request.sample_number} was created "
                    f"successfully and added to invoice "
                    f"{invoice.invoice_number}."
                )
            )

            return redirect("lab_requests")

    else:

        form = LabRequestForm()

    return render(
        request,
        "laboratory/lab_request_form.html",
        {
            "form": form
        }
    )


# =========================================================
# LAB REQUEST LIST
# =========================================================

@login_required
def lab_requests(request):

    requests = (
        LabRequest.objects
        .select_related(
            "patient",
            "test",
            "requested_by",
            "encounter",
        )
        .all()
    )

    # -----------------------------------------------------
    # SEARCH
    # -----------------------------------------------------

    search = request.GET.get(
        "q",
        ""
    ).strip()

    if search:

        requests = (
            requests.filter(
                patient__first_name__icontains=search
            )
            |
            requests.filter(
                patient__last_name__icontains=search
            )
            |
            requests.filter(
                patient__patient_number__icontains=search
            )
            |
            requests.filter(
                sample_number__icontains=search
            )
            |
            requests.filter(
                test__name__icontains=search
            )
        ).distinct()

    # -----------------------------------------------------
    # STATUS FILTER
    # -----------------------------------------------------

    status = request.GET.get(
        "status",
        ""
    ).strip()

    if status:

        status_map = {
            "PENDING": "Pending",
            "SAMPLE_COLLECTED": "Sample Collected",
            "PROCESSING": "Processing",
            "COMPLETED": "Completed",
        }

        selected_status = status_map.get(
            status,
            status
        )

        requests = requests.filter(
            status=selected_status
        )

    # -----------------------------------------------------
    # CONTEXT
    # -----------------------------------------------------

    context = {
        "lab_requests": requests,

        "total_requests": requests.count(),

        "pending_requests": requests.filter(
            status="Pending"
        ).count(),

        "processing_requests": requests.filter(
            status="Processing"
        ).count(),

        "completed_requests": requests.filter(
            status="Completed"
        ).count(),
    }

    return render(
        request,
        "laboratory/lab_request_list.html",
        context
    )


# =========================================================
# ENTER LAB RESULT
# =========================================================

@login_required
@transaction.atomic
def enter_result(request, id):

    lab_request = get_object_or_404(
        LabRequest.objects.select_related(
            "patient",
            "test",
            "encounter",
        ),
        id=id
    )

    # -----------------------------------------------------
    # PREVENT DUPLICATE RESULT
    # -----------------------------------------------------

    if hasattr(
        lab_request,
        "result_record"
    ):

        messages.info(
            request,
            (
                f"A result already exists for laboratory "
                f"request {lab_request.sample_number}."
            )
        )

        return redirect(
            "lab_requests"
        )

    # -----------------------------------------------------
    # RESULT FORM
    # -----------------------------------------------------

    if request.method == "POST":

        form = LabResultForm(
            request.POST
        )

        if form.is_valid():

            result = form.save(
                commit=False
            )

            result.lab_request = lab_request

            result.technician = request.user

            result.save()

            lab_request.status = "Completed"

            lab_request.save(
                update_fields=["status"]
            )

            messages.success(
                request,
                (
                    f"Laboratory result for "
                    f"{lab_request.sample_number} "
                    "was recorded successfully."
                )
            )

            return redirect(
                "lab_requests"
            )

    else:

        form = LabResultForm()

    return render(
        request,
        "laboratory/result_form.html",
        {
            "form": form,
            "request": lab_request,
        }
    )


# =========================================================
# PATIENT LAB RESULTS API
# =========================================================

@login_required
def patient_lab_results(
    request,
    patient_id
):

    results = (
        LabResult.objects
        .select_related(
            "lab_request",
            "lab_request__test",
            "lab_request__patient",
            "lab_request__encounter",
            "technician",
        )
        .filter(
            lab_request__patient_id=patient_id,
            lab_request__status="Completed",
        )
        .order_by(
            "-result_date"
        )
    )

    data = []

    for result in results:

        technician_name = "Not recorded"

        if result.technician:

            technician_name = (
                result.technician.get_full_name()
                or result.technician.username
            )

        data.append({

            "test":
                result.lab_request.test.name,

            "category":
                result.lab_request.test.category,

            "result":
                result.result,

            "interpretation":
                (
                    result.interpretation
                    or "No interpretation provided"
                ),

            "technician":
                technician_name,

            "sample_number":
                result.lab_request.sample_number,

            "date":
                result.result_date.strftime(
                    "%d %b %Y %H:%M"
                ),
        })

    return JsonResponse(
        data,
        safe=False
    )
