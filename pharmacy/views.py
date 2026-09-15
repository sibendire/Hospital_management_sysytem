from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.db.models import F
from django.contrib import messages
from django.db import transaction
from decimal import Decimal

from .models import (
    Medicine,
    PharmacySale,
    PharmacySaleItem,
    PharmacyAuditLog,
    Prescription,
    PrescriptionItem,
)

# from .forms import (
#     MedicineForm,
#     PrescriptionForm,
#     PrescriptionItemForm,
# )
from laboratory.models import LabRequest, LabResult
from django.db.models import (
    F,
    Sum,
    Count,
    Q,
    DecimalField,
    ExpressionWrapper,
)
from django.db.models.functions import Coalesce
from django.http import HttpResponse
from django.utils.dateparse import parse_date

from datetime import timedelta
# from io import BytesIO
# from openpyxl import Workbook
# from reportlab.lib import colors
# from reportlab.lib.pagesizes import A4, landscape
# from reportlab.lib.styles import getSampleStyleSheet
# from reportlab.platypus import (
#     SimpleDocTemplate,
#     Table,
#     TableStyle,
#     Paragraph,
#     Spacer,
# )


# =========================================================
# PHARMACY DASHBOARD
# =========================================================

def pharmacy_dashboard(request):

    today = timezone.now().date()

    medicine_count = Medicine.objects.count()

    low_stock = Medicine.objects.filter(
        quantity__gt=0,
        quantity__lte=F("reorder_level")
    ).count()

    out_of_stock = Medicine.objects.filter(
        quantity=0
    ).count()

    expired = Medicine.objects.filter(
        expiry_date__lt=today
    ).count()

    available_stock = Medicine.objects.filter(
        quantity__gt=0
    ).count()

    expiring_soon = Medicine.objects.filter(
        expiry_date__gte=today,
        expiry_date__lte=today + timezone.timedelta(days=30)
    ).count()

    context = {
        "medicine_count": medicine_count,
        "low_stock": low_stock,
        "out_of_stock": out_of_stock,
        "expired": expired,
        "available_stock": available_stock,
        "expiring_soon": expiring_soon,
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

    today = timezone.now().date()

    medicines = Medicine.objects.all().order_by("name")

    medicine_count = medicines.count()

    low_stock_count = Medicine.objects.filter(
        quantity__gt=0,
        quantity__lte=F("reorder_level")
    ).count()

    out_of_stock_count = Medicine.objects.filter(
        quantity=0
    ).count()

    thirty_days = today + timezone.timedelta(days=30)

    expiring_soon_count = Medicine.objects.filter(
        expiry_date__gte=today,
        expiry_date__lte=thirty_days
    ).count()

    context = {
        "medicines": medicines,
        "medicine_count": medicine_count,
        "low_stock_count": low_stock_count,
        "out_of_stock_count": out_of_stock_count,
        "expiring_soon_count": expiring_soon_count,
    }

    return render(
        request,
        "pharmacy/medicine_list.html",
        context
    )


# =========================================================
# ADD MEDICINE
# =========================================================

def add_medicine(request):

    if request.method == "POST":

        form = MedicineForm(request.POST)

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Medicine added successfully."
            )

            return redirect("medicine_list")

        print("FORM ERRORS:")
        print(form.errors)

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

            messages.success(
                request,
                f"{medicine.name} updated successfully."
            )

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

        medicine_name = medicine.name

        medicine.delete()

        messages.success(
            request,
            f"{medicine_name} deleted successfully."
        )

        return redirect("medicine_list")

    return render(
        request,
        "pharmacy/medicine_confirm_delete.html",
        {
            "medicine": medicine
        }
    )


# =========================================================
# DISPENSE MEDICINE
# =========================================================
@login_required
@transaction.atomic
def dispense_medicine(request):

    if request.method == "POST":

        # ... validation ...

        sale = PharmacySale.objects.create(
            patient_name=patient_name,
            patient_number=patient_number,
            issued_by=request.user,
            total_amount=grand_total,
            payment_status="PENDING"
        )

        for item in sale_items:

            PharmacySaleItem.objects.create(
                sale=sale,
                medicine=item["medicine"],
                quantity=item["quantity"],
                unit_price=item["unit_price"],
                cost_price=item["cost_price"],
                total_price=item["total_price"]
            )

            medicine = item["medicine"]

            medicine.quantity -= item["quantity"]

            medicine.save(
                update_fields=[
                    "quantity",
                    "updated_at"
                ]
            )

        # =================================================
        # AUDIT LOG
        # =================================================

        PharmacyAuditLog.objects.create(
            user=request.user,
            action="MEDICINE_DISPENSED",
            reference=sale.sale_number,
            description=(
                f"Pharmacy sale {sale.sale_number} created for "
                f"{patient_name}. Total amount: "
                f"UGX {grand_total}"
            ),
            ip_address=request.META.get("REMOTE_ADDR")
        )

        messages.success(
            request,
            f"Medicine issue completed successfully. "
            f"Bill {sale.sale_number} created."
        )

        return redirect(
            "pharmacy_receipt",
            sale_id=sale.id
        )

    medicines = (
        Medicine.objects
        .filter(
            quantity__gt=0,
            status="ACTIVE"
        )
        .order_by("name")
    )

    return render(
        request,
        "pharmacy/dispense_medicine.html",
        {
            "medicines": medicines
        }
    )


# =========================================================
# MEDICINE SALES HISTORY
# =========================================================

def medicine_sales(request):

    sales = (
        PharmacySale.objects
        .select_related("issued_by")
        .prefetch_related("items__medicine")
        .all()
        .order_by("-sale_date", "-id")
    )

    return render(
        request,
        "pharmacy/medicine_sales.html",
        {
            "sales": sales
        }
    )


# =========================================================
# PHARMACY RECEIPT
# =========================================================

def pharmacy_receipt(request, sale_id):

    sale = get_object_or_404(
        PharmacySale.objects
        .prefetch_related("items__medicine")
        .select_related("issued_by"),
        id=sale_id
    )

    return render(
        request,
        "pharmacy/pharmacy_receipt.html",
        {
            "sale": sale
        }
    )
@login_required
@transaction.atomic
def confirm_pharmacy_payment(request, sale_id):

    if request.method != "POST":
        return redirect("medicine_sales")

    sale = (
        PharmacySale.objects
        .select_for_update()
        .get(id=sale_id)
    )

    # Prevent paying the same bill twice
    if sale.payment_status == "PAID":

        messages.warning(
            request,
            f"Bill {sale.sale_number} has already been paid."
        )

        return redirect("medicine_sales")

    # Make sure the bill is still payable
    if sale.payment_status != "PENDING":

        messages.error(
            request,
            "This bill cannot be paid."
        )

        return redirect("medicine_sales")

    payment_method = request.POST.get(
        "payment_method"
    )

    if payment_method not in [
        "CASH",
        "MOBILE_MONEY",
        "CARD",
        "INSURANCE",
    ]:

        messages.error(
            request,
            "Please select a valid payment method."
        )

        return redirect("medicine_sales")

    paid_amount = sale.total_amount

    sale.payment_status = "PAID"
    sale.payment_method = payment_method
    sale.amount_paid = paid_amount
    sale.paid_by = request.user
    sale.paid_at = timezone.now()

    sale.save(
    update_fields=[
        "payment_status",
        "payment_method",
        "amount_paid",
        "paid_by",
        "paid_at",
        "updated_at",
    ]
)

    messages.success(
        request,
        f"Payment for bill {sale.sale_number} "
        f"has been confirmed successfully."
    )

    return redirect(
        "pharmacy_receipt",
        sale_id=sale.id
    )
@login_required
def prescription_details(request, pk):

    prescription = get_object_or_404(
        Prescription.objects
        .select_related(
            "patient",
            "prescribed_by"
        )
        .prefetch_related(
            "items__medicine"
        ),
        pk=pk
    )

    return render(
        request,
        "pharmacy/prescription_details.html",
        {
            "prescription": prescription
        }
    )
@login_required
def prescription_list(request):

    prescriptions = (
        Prescription.objects
        .select_related(
            "patient",
            "prescribed_by"
        )
        .prefetch_related(
            "items__medicine"
        )
        .order_by("-prescribed_at")
    )

    return render(
        request,
        "pharmacy/prescription_list.html",
        {
            "prescriptions": prescriptions
        }
    )

    # =========================================================
# CREATE PRESCRIPTION
# =========================================================

@login_required
@transaction.atomic
def create_prescription(request):

    if request.method == "POST":

        prescription_form = PrescriptionForm(request.POST)

        if prescription_form.is_valid():

            prescription = prescription_form.save(
                commit=False
            )

            prescription.prescribed_by = request.user

            prescription.save()

            # ---------------------------------------------
            # PRESCRIPTION ITEMS
            # ---------------------------------------------

            medicine_ids = request.POST.getlist(
                "medicine[]"
            )

            dosages = request.POST.getlist(
                "dosage[]"
            )

            frequencies = request.POST.getlist(
                "frequency[]"
            )

            durations = request.POST.getlist(
                "duration[]"
            )

            quantities = request.POST.getlist(
                "quantity[]"
            )

            instructions = request.POST.getlist(
                "instructions[]"
            )

            for i in range(len(medicine_ids)):

                if not medicine_ids[i]:
                    continue

                medicine = get_object_or_404(
                    Medicine,
                    id=medicine_ids[i],
                    status="ACTIVE"
                )

                quantity = int(
                    quantities[i]
                )

                PrescriptionItem.objects.create(

                    prescription=prescription,

                    medicine=medicine,

                    dosage=dosages[i],

                    frequency=frequencies[i],

                    duration=durations[i],

                    quantity=quantity,

                    instructions=(
                        instructions[i]
                        if i < len(instructions)
                        else ""
                    )
                )

            messages.success(
                request,
                f"Prescription #{prescription.id} "
                f"created successfully."
            )

            return redirect(
                "prescription_details",
                pk=prescription.id
            )

    else:

        prescription_form = PrescriptionForm()

    # ---------------------------------------------
    # PATIENT
    # ---------------------------------------------

    patient_id = request.GET.get(
        "patient"
    )

    lab_results = LabResult.objects.none()

    if patient_id:

        lab_results = (
            LabResult.objects
            .select_related(
                "lab_request",
                "lab_request__test"
            )
            .filter(
                lab_request__patient_id=patient_id,
                lab_request__status="Completed"
            )
            .order_by(
                "-result_date"
            )
        )

    # ---------------------------------------------
    # MEDICINES
    # ---------------------------------------------

    medicines = (
        Medicine.objects
        .filter(
            status="ACTIVE",
            quantity__gt=0
        )
        .order_by("name")
    )

    return render(
        request,
        "pharmacy/create_prescription.html",
        {
            "prescription_form": prescription_form,
            "medicines": medicines,
            "lab_results": lab_results,
            "selected_patient": patient_id,
        }
    )

# =========================================================
# PHARMACY REPORTS
# =========================================================

@login_required
def pharmacy_reports(request):

    today = timezone.now().date()

    date_from = request.GET.get("date_from")
    date_to = request.GET.get("date_to")
    category = request.GET.get("category")
    payment_method = request.GET.get("payment_method")

    if not date_from:
        date_from = today.replace(day=1).isoformat()

    if not date_to:
        date_to = today.isoformat()

    start_date = parse_date(date_from)
    end_date = parse_date(date_to)

    if not start_date:
        start_date = today.replace(day=1)

    if not end_date:
        end_date = today

    end_datetime = timezone.make_aware(
        timezone.datetime.combine(
            end_date + timedelta(days=1),
            timezone.datetime.min.time()
        )
    )

    start_datetime = timezone.make_aware(
        timezone.datetime.combine(
            start_date,
            timezone.datetime.min.time()
        )
    )

    # -----------------------------------------------------
    # SALES
    # -----------------------------------------------------

    sales = PharmacySale.objects.filter(
        sale_date__gte=start_datetime,
        sale_date__lt=end_datetime
    )

    if payment_method:
        sales = sales.filter(
            payment_method=payment_method
        )

    total_sales = sales.count()

    total_revenue = (
        sales.filter(payment_status="PAID")
        .aggregate(
            total=Coalesce(
                Sum("amount_paid"),
                Decimal("0.00")
            )
        )["total"]
    )

    outstanding = (
        sales.filter(
            payment_status__in=["PENDING", "PARTIAL"]
        )
        .aggregate(
            total=Coalesce(
                Sum(
                    ExpressionWrapper(
                        F("total_amount") - F("amount_paid"),
                        output_field=DecimalField(
                            max_digits=12,
                            decimal_places=2
                        )
                    )
                ),
                Decimal("0.00")
            )
        )["total"]
    )

    total_billed = (
        sales.aggregate(
            total=Coalesce(
                Sum("total_amount"),
                Decimal("0.00")
            )
        )["total"]
    )

    # -----------------------------------------------------
    # SALE ITEMS
    # -----------------------------------------------------

    sale_items = PharmacySaleItem.objects.filter(
        sale__sale_date__gte=start_datetime,
        sale__sale_date__lt=end_datetime
    )

    if category:
        sale_items = sale_items.filter(
            medicine__category=category
        )

    total_items_sold = (
        sale_items.aggregate(
            total=Coalesce(
                Sum("quantity"),
                0
            )
        )["total"]
    )

    total_cost = (
        sale_items.aggregate(
            total=Coalesce(
                Sum(
                    ExpressionWrapper(
                        F("cost_price") * F("quantity"),
                        output_field=DecimalField(
                            max_digits=14,
                            decimal_places=2
                        )
                    )
                ),
                Decimal("0.00")
            )
        )["total"]
    )

    total_profit = (
        sale_items.aggregate(
            total=Coalesce(
                Sum(
                    ExpressionWrapper(
                        F("total_price")
                        - (
                            F("cost_price")
                            * F("quantity")
                        ),
                        output_field=DecimalField(
                            max_digits=14,
                            decimal_places=2
                        )
                    )
                ),
                Decimal("0.00")
            )
        )["total"]
    )

    if total_revenue:
        profit_margin = (
            total_profit / total_revenue
        ) * Decimal("100")
    else:
        profit_margin = Decimal("0.00")

    # -----------------------------------------------------
    # INVENTORY
    # -----------------------------------------------------

    medicines = Medicine.objects.all()

    inventory_value = (
        medicines.aggregate(
            total=Coalesce(
                Sum(
                    ExpressionWrapper(
                        F("quantity") * F("cost_price"),
                        output_field=DecimalField(
                            max_digits=16,
                            decimal_places=2
                        )
                    )
                ),
                Decimal("0.00")
            )
        )["total"]
    )

    selling_value = (
        medicines.aggregate(
            total=Coalesce(
                Sum(
                    ExpressionWrapper(
                        F("quantity") * F("unit_price"),
                        output_field=DecimalField(
                            max_digits=16,
                            decimal_places=2
                        )
                    )
                ),
                Decimal("0.00")
            )
        )["total"]
    )

    low_stock = medicines.filter(
        quantity__gt=0,
        quantity__lte=F("reorder_level")
    ).count()

    out_of_stock = medicines.filter(
        quantity=0
    ).count()

    expired = medicines.filter(
        expiry_date__lt=today
    ).count()

    expiring_30 = medicines.filter(
        expiry_date__gte=today,
        expiry_date__lte=today + timedelta(days=30)
    ).count()

    # -----------------------------------------------------
    # PRESCRIPTIONS
    # -----------------------------------------------------

    prescriptions = Prescription.objects.filter(
        prescribed_at__gte=start_datetime,
        prescribed_at__lt=end_datetime
    )

    prescription_count = prescriptions.count()

    pending_prescriptions = prescriptions.filter(
        status="PENDING"
    ).count()

    dispensed_prescriptions = prescriptions.filter(
        status="DISPENSED"
    ).count()

    # -----------------------------------------------------
    # PAYMENT BREAKDOWN
    # -----------------------------------------------------

    payment_breakdown = (
        sales.filter(payment_status="PAID")
        .values("payment_method")
        .annotate(
            total=Sum("amount_paid"),
            count=Count("id")
        )
        .order_by("-total")
    )

    # -----------------------------------------------------
    # CATEGORY BREAKDOWN
    # -----------------------------------------------------

    category_breakdown = (
        sale_items
        .values(
            "medicine__category"
        )
        .annotate(
            quantity=Sum("quantity"),
            revenue=Sum("total_price")
        )
        .order_by("-revenue")
    )

    # -----------------------------------------------------
    # FAST MOVING
    # -----------------------------------------------------

    fast_moving = (
        sale_items
        .values(
            "medicine__name"
        )
        .annotate(
            quantity_sold=Sum("quantity"),
            revenue=Sum("total_price")
        )
        .order_by("-quantity_sold")[:10]
    )

    # -----------------------------------------------------
    # SLOW MOVING
    # -----------------------------------------------------

    slow_moving = (
        sale_items
        .values(
            "medicine__name"
        )
        .annotate(
            quantity_sold=Sum("quantity"),
            revenue=Sum("total_price")
        )
        .order_by("quantity_sold")[:10]
    )

    # -----------------------------------------------------
    # EXPIRY
    # -----------------------------------------------------

    expiry_date_90 = today + timedelta(days=90)

    expiry_medicines = medicines.filter(
        expiry_date__lte=expiry_date_90
    ).order_by("expiry_date")

    context = {
        "date_from": start_date,
        "date_to": end_date,

        "total_sales": total_sales,
        "total_billed": total_billed,
        "total_revenue": total_revenue,
        "outstanding": outstanding,

        "total_items_sold": total_items_sold,
        "total_cost": total_cost,
        "total_profit": total_profit,
        "profit_margin": profit_margin,

        "inventory_value": inventory_value,
        "selling_value": selling_value,

        "low_stock": low_stock,
        "out_of_stock": out_of_stock,
        "expired": expired,
        "expiring_30": expiring_30,

        "prescription_count": prescription_count,
        "pending_prescriptions": pending_prescriptions,
        "dispensed_prescriptions": dispensed_prescriptions,

        "payment_breakdown": payment_breakdown,
        "category_breakdown": category_breakdown,

        "fast_moving": fast_moving,
        "slow_moving": slow_moving,

        "expiry_medicines": expiry_medicines,

        "categories": Medicine.CATEGORY_CHOICES,
        "payment_methods": PharmacySale.PAYMENT_METHOD_CHOICES,
    }

    return render(
        request,
        "pharmacy/reports.html",
        context
    )