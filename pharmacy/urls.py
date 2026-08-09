from django.urls import path

from . import views


urlpatterns = [

    path(

        "dashboard/",

        views.pharmacy_dashboard,

        name="pharmacy_dashboard"

    ),

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

]