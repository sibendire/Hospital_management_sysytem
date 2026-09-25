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
def get_or_create_invoice(
    patient,
    encounter=None,
):

    if not patient:

        raise ValidationError(
            "A patient is required to create an invoice."
        )

    # -----------------------------------------------------
    # Reuse ONLY an open invoice
    # -----------------------------------------------------

    invoice_query = (
        Invoice.objects
        .filter(
            patient=patient,
            payment_status__in=[
                "UNPAID",
                "PARTIAL",
            ],
        )
        .exclude(
            status="CANCELLED"
        )
    )

    if encounter:

        invoice = (
            invoice_query
            .filter(
                encounter=encounter
            )
            .order_by("-invoice_date")
            .first()
        )

    else:

        invoice = (
            invoice_query
            .filter(
                encounter__isnull=True
            )
            .order_by("-invoice_date")
            .first()
        )

    if invoice:

        return invoice

    # -----------------------------------------------------
    # Create new invoice
    # -----------------------------------------------------

    return Invoice.objects.create(
        patient=patient,
        encounter=encounter,
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

    # -----------------------------------------------------
    # Prevent duplicate source charges
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # Create item
    # -----------------------------------------------------

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
def add_pharmacy_charge(
    pharmacy_sale,
):

    if not pharmacy_sale.patient:

        raise ValidationError(
            "A patient is required for a pharmacy charge."
        )

    invoice = get_or_create_invoice(
        patient=pharmacy_sale.patient,
        encounter=pharmacy_sale.encounter,
    )

    created_items = []

    for sale_item in pharmacy_sale.items.select_related(
        "medicine"
    ):

        item = add_invoice_item(
            invoice=invoice,
            service_type="PHARMACY",
            description=(
                f"{sale_item.medicine.name} "
                f"x {sale_item.quantity}"
            ),
            quantity=sale_item.quantity,
            unit_price=sale_item.selling_price,
            source_type="PHARMACY_SALE_ITEM",
            source_id=sale_item.id,
        )

        created_items.append(item)

    return invoice, created_items


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