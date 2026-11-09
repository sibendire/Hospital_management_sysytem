from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction

from .models import (
    Invoice,
    InvoiceItem,
)



# =========================================================
# GET OR CREATE OPEN INVOICE
# =========================================================

@transaction.atomic
def get_or_create_invoice(patient, encounter=None):

    if not patient:
        raise ValidationError(
            "A patient is required to create an invoice."
        )

    # -----------------------------------------------------
    # ENCOUNTER BILLING
    # -----------------------------------------------------

    if encounter:

        invoice = (
            Invoice.objects
            .select_for_update()
            .filter(
                patient=patient,
                encounter=encounter,
                payment_status__in=[
                    "UNPAID",
                    "PARTIAL",
                ],
            )
            .exclude(
                status__in=[
                    "PAID",
                    "CANCELLED",
                ]
            )
            .exclude(
                payment_status="CANCELLED"
            )
            .order_by("-invoice_date", "-id")
            .first()
        )

        if invoice:
            return invoice

        # No open invoice exists.
        # Create a new invoice instead of reopening
        # a paid or cancelled invoice.

        return Invoice.objects.create(
            patient=patient,
            encounter=encounter,
            status="UNPAID",
            payment_status="UNPAID",
        )

    # -----------------------------------------------------
    # PATIENT-LEVEL BILLING WITHOUT ENCOUNTER
    # -----------------------------------------------------

    invoice = (
        Invoice.objects
        .select_for_update()
        .filter(
            patient=patient,
            encounter__isnull=True,
            payment_status__in=[
                "UNPAID",
                "PARTIAL",
            ],
        )
        .exclude(
            status__in=[
                "PAID",
                "CANCELLED",
            ]
        )
        .exclude(
            payment_status="CANCELLED"
        )
        .order_by("-invoice_date", "-id")
        .first()
    )

    if invoice:
        return invoice

    return Invoice.objects.create(
        patient=patient,
        encounter=None,
        status="UNPAID",
        payment_status="UNPAID",
    )

# =========================================================
# ADD INVOICE ITEM
# =========================================================

@transaction.atomic
def add_invoice_item(
    invoice,
    service_type,
    description,
    quantity=1,
    unit_price=Decimal("0.00"),
    source_type=None,
    source_id=None,
):

    invoice = (
        Invoice.objects
        .select_for_update()
        .get(
            pk=invoice.pk
        )
    )

    if invoice.status in [
        "PAID",
        "CANCELLED",
    ]:

        raise ValidationError(
            "Cannot add charges to a paid or cancelled invoice."
        )

    try:

        quantity = int(quantity)

    except (
        TypeError,
        ValueError,
    ):

        raise ValidationError(
            "Quantity must be a valid number."
        )

    try:

        unit_price = Decimal(
            str(unit_price)
        )

    except Exception:

        raise ValidationError(
            "Unit price must be a valid amount."
        )

    if quantity <= 0:

        raise ValidationError(
            "Quantity must be greater than zero."
        )

    if unit_price < 0:

        raise ValidationError(
            "Unit price cannot be negative."
        )

    if source_type and source_id:

        existing_item = (
            InvoiceItem.objects
            .filter(
                invoice=invoice,
                source_type=source_type,
                source_id=source_id,
            )
            .first()
        )

        if existing_item:

            return existing_item

    item = InvoiceItem.objects.create(
        invoice=invoice,
        service_type=service_type,
        description=description,
        quantity=quantity,
        unit_price=unit_price,
        source_type=source_type,
        source_id=source_id,
    )

    invoice.update_payment_status()

    return item


# =========================================================
# LABORATORY CHARGE
# =========================================================

@transaction.atomic
def add_lab_charge(
    lab_request,
):

    if not lab_request.patient:

        raise ValidationError(
            "A patient is required for a laboratory charge."
        )

    if not lab_request.test:

        raise ValidationError(
            "A laboratory test is required for a laboratory charge."
        )

    invoice = get_or_create_invoice(
        patient=lab_request.patient,
        encounter=lab_request.encounter,
    )

    item = add_invoice_item(
        invoice=invoice,
        service_type="LABORATORY",
        description=(
            f"Laboratory Test: "
            f"{lab_request.test.name}"
        ),
        quantity=1,
        unit_price=lab_request.test.price,
        source_type="LAB_REQUEST",
        source_id=lab_request.id,
    )

    return invoice, item



# =========================================================
# PHARMACY CHARGE
# =========================================================

@transaction.atomic
def add_pharmacy_charge(pharmacy_sale):

    if not pharmacy_sale.patient:
        raise ValidationError(
            "A patient is required for pharmacy billing."
        )

    if not pharmacy_sale.encounter:
        raise ValidationError(
            "A clinical encounter is required for pharmacy billing."
        )

    sale_items = list(
        pharmacy_sale.items
        .select_related("medicine")
        .all()
    )

    if not sale_items:
        raise ValidationError(
            "The pharmacy sale has no items to bill."
        )

    # -----------------------------------------------------
    # CHECK WHETHER ALL SALE ITEMS WERE ALREADY BILLED
    # -----------------------------------------------------

    existing_items = {
        item.source_id: item
        for item in InvoiceItem.objects
        .select_related("invoice")
        .filter(
            source_type="PHARMACY_SALE_ITEM",
            source_id__in=[
                sale_item.id for sale_item in sale_items
            ],
        )
    }

    # If every item is already billed, return its
    # original invoice without creating another invoice.

    if len(existing_items) == len(sale_items):

        existing_invoices = {
            item.invoice_id: item.invoice
            for item in existing_items.values()
        }

        if len(existing_invoices) != 1:
            raise ValidationError(
                "The pharmacy sale items are linked to "
                "multiple invoices. Please review the billing records."
            )

        invoice = next(
            iter(existing_invoices.values())
        )

        return invoice, list(existing_items.values())

    # -----------------------------------------------------
    # GET AN OPEN INVOICE
    # -----------------------------------------------------

    invoice = get_or_create_invoice(
        patient=pharmacy_sale.patient,
        encounter=pharmacy_sale.encounter,
    )

    created_items = []

    # -----------------------------------------------------
    # BILL ONLY ITEMS NOT PREVIOUSLY BILLED
    # -----------------------------------------------------

    for sale_item in sale_items:

        if sale_item.id in existing_items:
            continue

        medicine_name = sale_item.medicine.name

        if getattr(
            sale_item.medicine,
            "strength",
            None
        ):
            medicine_name = (
                f"{medicine_name} "
                f"{sale_item.medicine.strength}"
            )

        item = add_invoice_item(
            invoice=invoice,
            service_type="PHARMACY",
            description=(
                f"Pharmacy: {medicine_name} "
                f"x {sale_item.quantity}"
            ),
            quantity=sale_item.quantity,
            unit_price=sale_item.selling_price,
            source_type="PHARMACY_SALE_ITEM",
            source_id=sale_item.id,
        )

        created_items.append(item)

    # -----------------------------------------------------
    # REFRESH INVOICE
    # -----------------------------------------------------

    invoice.refresh_from_db()

    invoice.update_payment_status()

    invoice.refresh_from_db()

    all_billed_items = [
        existing_items[sale_item.id]
        if sale_item.id in existing_items
        else next(
            item for item in created_items
            if item.source_id == sale_item.id
        )
        for sale_item in sale_items
    ]

    return invoice, all_billed_items

# =========================================================
# CONSULTATION CHARGE
# =========================================================

@transaction.atomic
def add_consultation_charge(
    encounter,
    amount,
    description="Doctor Consultation",
):

    if not encounter.patient:

        raise ValidationError(
            "A patient is required for a consultation charge."
        )

    try:

        amount = Decimal(
            str(amount)
        )

    except Exception:

        raise ValidationError(
            "Consultation amount must be a valid amount."
        )

    if amount < 0:

        raise ValidationError(
            "Consultation amount cannot be negative."
        )

    invoice = get_or_create_invoice(
        patient=encounter.patient,
        encounter=encounter,
    )

    item = add_invoice_item(
        invoice=invoice,
        service_type="CONSULTATION",
        description=description,
        quantity=1,
        unit_price=amount,
        source_type="CLINICAL_ENCOUNTER",
        source_id=encounter.id,
    )

    return invoice, item