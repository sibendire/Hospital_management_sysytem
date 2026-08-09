from django.urls import path
from . import views


urlpatterns = [

    path(
        "dashboard/",
        views.billing_dashboard,
        name="billing_dashboard"
    ),

    path(
        "invoices/",
        views.invoice_list,
        name="invoice_list"
    ),

    path(
        "invoice/create/",
        views.create_invoice,
        name="create_invoice"
    ),

    path(
        "invoice/<int:invoice_id>/",
        views.invoice_detail,
        name="invoice_detail"
    ),

    path(
        "invoice/<int:invoice_id>/item/add/",
        views.add_invoice_item,
        name="add_invoice_item"
    ),

    path(
        "invoice/item/<int:item_id>/delete/",
        views.delete_invoice_item,
        name="delete_invoice_item"
    ),

    path(
        "invoice/<int:invoice_id>/payment/",
        views.record_payment,
        name="record_payment"
    ),

    path(
        "payments/",
        views.payment_list,
        name="payment_list"
    ),

    path(
        "payment/<int:payment_id>/receipt/",
        views.receipt,
        name="receipt"
    ),

    path(
        "reports/",
        views.billing_reports,
        name="billing_reports"
    ),
]