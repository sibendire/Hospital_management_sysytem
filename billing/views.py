from django.shortcuts import render

# Create your views here.


from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import (
    render,
    redirect,
    get_object_or_404
)
from django.utils import timezone

from .models import (
    Invoice,
    InvoiceItem,
    Payment
)

from .forms import (
    InvoiceForm,
    InvoiceItemForm,
    PaymentForm
)


@login_required
def billing_dashboard(request):

    today = timezone.localdate()

    invoices_today = Invoice.objects.filter(
        invoice_date__date=today
    )

    payments_today = Payment.objects.filter(
        payment_date__date=today,
        status="COMPLETED"
    )

    today_revenue = (
        payments_today.aggregate(
            total=Sum("amount")
        )["total"]
        or Decimal("0.00")
    )

    total_invoices = Invoice.objects.count()

    unpaid_invoices = Invoice.objects.filter(
        payment_status="UNPAID"
    ).count()

    partial_invoices = Invoice.objects.filter(
        payment_status="PARTIAL"
    ).count()

    paid_invoices = Invoice.objects.filter(
        payment_status="PAID"
    ).count()

    outstanding = Decimal("0.00")

    for invoice in Invoice.objects.exclude(
        status="CANCELLED"
    ):

        outstanding += invoice.balance

    recent_payments = Payment.objects.select_related(
        "invoice",
        "invoice__patient"
    ).filter(
        status="COMPLETED"
    )[:10]

    recent_invoices = Invoice.objects.select_related(
        "patient"
    )[:10]

    context = {

        "today_revenue": today_revenue,

        "total_invoices": total_invoices,

        "unpaid_invoices": unpaid_invoices,

        "partial_invoices": partial_invoices,

        "paid_invoices": paid_invoices,

        "outstanding": outstanding,

        "recent_payments": recent_payments,

        "recent_invoices": recent_invoices,

    }

    return render(
        request,
        "billing/dashboard.html",
        context
    )


@login_required
def invoice_list(request):

    invoices = Invoice.objects.select_related(
        "patient"
    ).order_by(
        "-invoice_date"
    )

    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()

    if query:
        invoices = invoices.filter(
            Q(invoice_number__icontains=query)
            | Q(patient__first_name__icontains=query)
            | Q(patient__last_name__icontains=query)
            | Q(patient__patient_number__icontains=query)
        )

    if status in ["UNPAID", "PARTIAL", "PAID"]:
        invoices = invoices.filter(
            payment_status=status
        )

    return render(
        request,
        "billing/invoice_list.html",
        {
            "invoices": invoices,
        }
    )


@login_required
def create_invoice(request):

    if request.method == "POST":

        form = InvoiceForm(request.POST)

        if form.is_valid():

            invoice = form.save(
                commit=False
            )

            invoice.created_by = (
                request.user.username
            )

            invoice.save()

            messages.success(
                request,
                f"Invoice {invoice.invoice_number} "
                f"created successfully."
            )

            return redirect(
                "invoice_detail",
                invoice_id=invoice.id
            )

    else:

        form = InvoiceForm()

    return render(
        request,
        "billing/invoice_form.html",
        {
            "form": form
        }
    )


@login_required
def invoice_detail(
    request,
    invoice_id
):

    invoice = get_object_or_404(
        Invoice.objects.select_related(
            "patient"
        ),
        id=invoice_id
    )

    items = invoice.items.all()

    payments = invoice.payments.filter(
        status="COMPLETED"
    )

    return render(
        request,
        "billing/invoice_detail.html",
        {
            "invoice": invoice,
            "items": items,
            "payments": payments,
        }
    )


@login_required
def add_invoice_item(
    request,
    invoice_id
):

    invoice = get_object_or_404(
        Invoice,
        id=invoice_id
    )

    if invoice.status == "PAID":

        messages.error(
            request,
            "A fully paid invoice cannot be modified."
        )

        return redirect(
            "invoice_detail",
            invoice_id=invoice.id
        )

    if invoice.status == "CANCELLED":

        messages.error(
            request,
            "A cancelled invoice cannot be modified."
        )

        return redirect(
            "invoice_detail",
            invoice_id=invoice.id
        )

    if request.method == "POST":

        form = InvoiceItemForm(
            request.POST
        )

        if form.is_valid():

            item = form.save(
                commit=False
            )

            item.invoice = invoice

            item.save()

            invoice.update_payment_status()

            messages.success(
                request,
                "Invoice item added successfully."
            )

            return redirect(
                "invoice_detail",
                invoice_id=invoice.id
            )

    else:

        form = InvoiceItemForm()

    return render(
        request,
        "billing/invoice_item_form.html",
        {
            "form": form,
            "invoice": invoice
        }
    )


@login_required
def delete_invoice_item(request, item_id):

    item = get_object_or_404(
        InvoiceItem,
        id=item_id
    )

    invoice = item.invoice

    if invoice.status == "PAID":

        messages.error(
            request,
            "A fully paid invoice cannot be modified."
        )

        return redirect(
            "invoice_detail",
            invoice_id=invoice.id
        )

    if invoice.status == "CANCELLED":

        messages.error(
            request,
            "A cancelled invoice cannot be modified."
        )

        return redirect(
            "invoice_detail",
            invoice_id=invoice.id
        )

    item.delete()

    invoice.update_payment_status()

    messages.success(
        request,
        "Invoice item removed successfully."
    )

    return redirect(
        "invoice_detail",
        invoice_id=invoice.id
    )

@login_required
def record_payment(request, invoice_id):

    invoice = get_object_or_404(
        Invoice.objects.select_related("patient"),
        id=invoice_id
    )

    # --------------------------------------------------
    # Prevent payment on cancelled invoice
    # --------------------------------------------------
    if invoice.status == "CANCELLED":

        messages.error(
            request,
            "Cannot receive payment for a cancelled invoice."
        )

        return redirect(
            "invoice_detail",
            invoice_id=invoice.id
        )

    # --------------------------------------------------
    # Calculate amount already paid
    # --------------------------------------------------
    paid_amount = (
        invoice.payments
        .filter(status="COMPLETED")
        .aggregate(
            total=Sum("amount")
        )["total"]
        or Decimal("0.00")
    )

    # --------------------------------------------------
    # Calculate invoice balance
    # --------------------------------------------------
    invoice_total = invoice.total_amount or Decimal("0.00")

    balance = invoice_total - paid_amount

    if balance <= Decimal("0.00"):

        messages.info(
            request,
            "This invoice has already been fully paid."
        )

        return redirect(
            "invoice_detail",
            invoice_id=invoice.id
        )

    # --------------------------------------------------
    # Process payment
    # --------------------------------------------------
    if request.method == "POST":

        form = PaymentForm(
            request.POST,
            invoice=invoice
        )

        if form.is_valid():

            payment = form.save(
                commit=False
            )

            payment.invoice = invoice

            payment.received_by = (
                request.user.username
            )

            payment.status = "COMPLETED"

            # --------------------------------------------------
            # Prevent payment exceeding invoice balance
            # --------------------------------------------------
            if payment.amount > balance:

                form.add_error(
                    "amount",
                    (
                        f"Payment cannot exceed the outstanding "
                        f"balance of UGX {balance:,.2f}."
                    )
                )

            else:

                payment.save()

                # Recalculate invoice payment status
                invoice.update_payment_status()

                messages.success(
                    request,
                    (
                        f"Payment of UGX "
                        f"{payment.amount:,.2f} "
                        f"received successfully."
                    )
                )

                return redirect(
                    "invoice_detail",
                    invoice_id=invoice.id
                )

    else:

        # --------------------------------------------------
        # Automatically fill the outstanding balance
        # --------------------------------------------------
        form = PaymentForm(
            invoice=invoice,
            initial={
                "amount": balance
            }
        )

    return render(
        request,
        "billing/payment_form.html",
        {
            "form": form,
            "invoice": invoice,
            "paid_amount": paid_amount,
            "balance": balance,
        }
    )


@login_required
def payment_list(request):

    payments = Payment.objects.select_related(
        "invoice",
        "invoice__patient"
    ).order_by(
        "-payment_date"
    )

    return render(
        request,
        "billing/payment_list.html",
        {
            "payments": payments
        }
    )


@login_required
def receipt(request, payment_id):

    payment = get_object_or_404(
        Payment.objects.select_related(
            "invoice",
            "invoice__patient"
        ),
        id=payment_id
    )

    return render(
        request,
        "billing/receipt.html",
        {
            "payment": payment
        }
    )


@login_required
def billing_reports(request):

    today = timezone.localdate()

    today_payments = Payment.objects.filter(
        payment_date__date=today,
        status="COMPLETED"
    )

    today_revenue = (
        today_payments.aggregate(
            total=Sum("amount")
        )["total"]
        or Decimal("0.00")
    )

    total_revenue = (
        Payment.objects.filter(
            status="COMPLETED"
        ).aggregate(
            total=Sum("amount")
        )["total"]
        or Decimal("0.00")
    )

    payment_methods = (
        Payment.objects.filter(
            status="COMPLETED"
        )
        .values(
            "payment_method"
        )
        .annotate(
            total=Sum("amount")
        )
        .order_by(
            "-total"
        )
    )

    return render(
        request,
        "billing/reports.html",
        {
            "today_revenue": today_revenue,
            "total_revenue": total_revenue,
            "payment_methods": payment_methods,
        }
    )