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
    Prescription,
    PrescriptionItem,
)

from .forms import (
    MedicineForm,
    PrescriptionForm,
    PrescriptionItemForm,
)


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

@transaction.atomic
def dispense_medicine(request):

    if request.method == "POST":

        patient_name = request.POST.get(
            "patient_name",
            ""
        ).strip()

        patient_number = request.POST.get(
            "patient_number",
            ""
        ).strip()

        medicine_ids = request.POST.getlist(
            "medicine_id[]"
        )

        quantities = request.POST.getlist(
            "quantity[]"
        )

        # -------------------------------------------------
        # VALIDATE PATIENT
        # -------------------------------------------------

        if not patient_name:

            messages.error(
                request,
                "Patient name is required."
            )

            return redirect("dispense_medicine")

        # -------------------------------------------------
        # VALIDATE MEDICINES
        # -------------------------------------------------

        if not medicine_ids:

            messages.error(
                request,
                "Please add at least one medicine."
            )

            return redirect("dispense_medicine")

        if len(medicine_ids) != len(quantities):

            messages.error(
                request,
                "Invalid medicine information."
            )

            return redirect("dispense_medicine")

        # -------------------------------------------------
        # PREPARE ITEMS
        # -------------------------------------------------

        sale_items = []

        grand_total = Decimal("0.00")

        # -------------------------------------------------
        # VALIDATE EVERYTHING
        # -------------------------------------------------

        for medicine_id, quantity_value in zip(
            medicine_ids,
            quantities
        ):

            try:

                quantity = int(quantity_value)

                if quantity <= 0:
                    raise ValueError

            except (ValueError, TypeError):

                messages.error(
                    request,
                    "Invalid medicine quantity."
                )

                return redirect("dispense_medicine")

            # -------------------------------------------------
            # LOCK MEDICINE
            # -------------------------------------------------

            medicine = (
                Medicine.objects
                .select_for_update()
                .filter(
                    id=medicine_id,
                    status="ACTIVE"
                )
                .first()
            )

            if not medicine:

                messages.error(
                    request,
                    "One of the selected medicines is unavailable."
                )

                return redirect("dispense_medicine")

            # -------------------------------------------------
            # CHECK EXPIRY
            # -------------------------------------------------

            if (
                medicine.expiry_date
                and medicine.expiry_date < timezone.now().date()
            ):

                messages.error(
                    request,
                    f"{medicine.name} has expired "
                    f"and cannot be issued."
                )

                return redirect("dispense_medicine")

            # -------------------------------------------------
            # CHECK STOCK
            # -------------------------------------------------

            if quantity > medicine.quantity:

                messages.error(
                    request,
                    f"Insufficient stock for {medicine.name}. "
                    f"Available: {medicine.quantity}, "
                    f"Requested: {quantity}."
                )

                return redirect("dispense_medicine")

            # -------------------------------------------------
            # CALCULATE PRICE
            # -------------------------------------------------

            unit_price = medicine.unit_price

            total_price = unit_price * quantity

            sale_items.append({
                "medicine": medicine,
                "quantity": quantity,
                "unit_price": unit_price,
                "total_price": total_price,
            })

            grand_total += total_price

        # -------------------------------------------------
        # CREATE SALE
        # -------------------------------------------------

        sale = PharmacySale.objects.create(
            patient_name=patient_name,
            patient_number=patient_number,
            issued_by=request.user,
            total_amount=grand_total,
            payment_status="PENDING"
        )

        # -------------------------------------------------
        # CREATE SALE ITEMS
        # AND DEDUCT STOCK
        # -------------------------------------------------

        for item in sale_items:

            PharmacySaleItem.objects.create(
                sale=sale,
                medicine=item["medicine"],
                quantity=item["quantity"],
                unit_price=item["unit_price"],
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

        # -------------------------------------------------
        # SUCCESS
        # -------------------------------------------------

        messages.success(
            request,
            f"Medicine issue completed successfully. "
            f"Bill {sale.sale_number} created."
        )

        return redirect(
            "pharmacy_receipt",
            sale_id=sale.id
        )

    # -----------------------------------------------------
    # GET
    # -----------------------------------------------------

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

    sale.paid_amount = paid_amount

    sale.paid_by = request.user

    sale.paid_at = timezone.now()

    sale.save(
        update_fields=[
            "payment_status",
            "payment_method",
            "paid_amount",
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

        prescription_form = PrescriptionForm(
            request.POST
        )

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

        # ---------------------------------------------
        # VALIDATE PRESCRIPTION
        # ---------------------------------------------

        if not prescription_form.is_valid():

            return render(
                request,
                "pharmacy/create_prescription.html",
                {
                    "prescription_form": prescription_form,
                    "medicines": Medicine.objects.filter(
                        status="ACTIVE",
                        quantity__gt=0
                    ).order_by("name"),
                }
            )

        # ---------------------------------------------
        # CHECK MEDICINES
        # ---------------------------------------------

        if not medicine_ids:

            messages.error(
                request,
                "Please add at least one medicine."
            )

            return redirect(
                "create_prescription"
            )

        # ---------------------------------------------
        # CHECK ARRAY LENGTHS
        # ---------------------------------------------

        if not (
            len(medicine_ids)
            == len(dosages)
            == len(frequencies)
            == len(durations)
            == len(quantities)
            == len(instructions)
        ):

            messages.error(
                request,
                "Invalid prescription medicine information."
            )

            return redirect(
                "create_prescription"
            )

        # ---------------------------------------------
        # CREATE PRESCRIPTION
        # ---------------------------------------------

        prescription = prescription_form.save(
            commit=False
        )

        prescription.prescribed_by = request.user

        prescription.status = "PENDING"

        prescription.save()

        # ---------------------------------------------
        # CREATE PRESCRIPTION ITEMS
        # ---------------------------------------------

        for i in range(len(medicine_ids)):

            try:

                medicine_id = medicine_ids[i]

                quantity = int(
                    quantities[i]
                )

                if quantity <= 0:
                    raise ValueError

            except (
                ValueError,
                TypeError
            ):

                messages.error(
                    request,
                    "Invalid medicine quantity."
                )

                raise transaction.TransactionManagementError(
                    "Invalid prescription quantity."
                )

            medicine = get_object_or_404(
                Medicine,
                id=medicine_id,
                status="ACTIVE"
            )

            # -----------------------------------------
            # CHECK EXPIRY
            # -----------------------------------------

            if medicine.expiry_date:

                if (
                    medicine.expiry_date
                    < timezone.now().date()
                ):

                    messages.error(
                        request,
                        f"{medicine.name} has expired."
                    )

                    raise transaction.TransactionManagementError(
                        "Expired medicine."
                    )

            # -----------------------------------------
            # CREATE ITEM
            # -----------------------------------------

            PrescriptionItem.objects.create(

                prescription=prescription,

                medicine=medicine,

                dosage=dosages[i].strip(),

                frequency=frequencies[i].strip(),

                duration=durations[i].strip(),

                quantity=quantity,

                instructions=instructions[i].strip()
                if instructions[i]
                else ""
            )

        # ---------------------------------------------
        # SUCCESS
        # ---------------------------------------------

        messages.success(
            request,
            f"Prescription #{prescription.id} "
            f"created successfully."
        )

        return redirect(
            "prescription_details",
            pk=prescription.id
        )

    # =================================================
    # GET
    # =================================================

    prescription_form = PrescriptionForm()

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
        }
    )