from django.urls import path
from . import views


urlpatterns = [

    # =====================================================
    # PHARMACY DASHBOARD
    # =====================================================

    path(
        "dashboard/",
        views.pharmacy_dashboard,
        name="pharmacy_dashboard"
    ),

    # =====================================================
    # MEDICINE INVENTORY
    # =====================================================

    path(
        "medicines/",
        views.medicine_list,
        name="medicine_list"
    ),

    path(
        "medicine/add/",
        views.add_medicine,
        name="add_medicine"
    ),

    path(
        "medicine/edit/<int:id>/",
        views.edit_medicine,
        name="edit_medicine"
    ),

    path(
        "medicine/delete/<int:id>/",
        views.delete_medicine,
        name="delete_medicine"
    ),

    # =====================================================
    # DISPENSING
    # =====================================================

    path(
        "medicine/dispense/",
        views.dispense_medicine,
        name="dispense_medicine"
    ),

    # Keep this alias if your existing dashboard/templates
    # already use {% url 'sell_medicine' %}

    path(
        "medicine/sell/",
        views.dispense_medicine,
        name="sell_medicine"
    ),

    # =====================================================
    # SALES
    # =====================================================

    path(
        "medicine/sales/",
        views.medicine_sales,
        name="medicine_sales"
    ),

    # =====================================================
    # RECEIPT
    # =====================================================

    path(
        "medicine/receipt/<int:sale_id>/",
        views.pharmacy_receipt,
        name="pharmacy_receipt"
    ),
      path(
        "medicine/payment/<int:sale_id>/",
        views.confirm_pharmacy_payment,
        name="confirm_pharmacy_payment"
    ),

  path(
    "prescriptions/",
    views.prescription_list,
    name="prescription_list"
),

path(
    "prescriptions/create/",
    views.create_prescription,
    name="create_prescription"
),

path(
    "prescriptions/<int:pk>/",
    views.prescription_details,
    name="prescription_details"
),
]