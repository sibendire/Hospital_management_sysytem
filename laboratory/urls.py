from django.urls import path

from . import views


app_name = "laboratory"


urlpatterns = [

    # =========================================================
    # LABORATORY DASHBOARD
    # =========================================================

    path(
        "",
        views.laboratory_dashboard,
        name="laboratory_dashboard"
    ),

    path(
        "dashboard/",
        views.laboratory_dashboard,
        name="dashboard"
    ),


    # =========================================================
    # LABORATORY TESTS
    # =========================================================

    path(
        "tests/",
        views.test_list,
        name="test_list"
    ),

    path(
        "tests/add/",
        views.add_test,
        name="add_test"
    ),

    path(
        "tests/<int:test_id>/edit/",
        views.edit_test,
        name="edit_test"
    ),

    path(
        "tests/<int:test_id>/delete/",
        views.delete_test,
        name="delete_test"
    ),


    # =========================================================
    # LABORATORY REQUESTS
    # =========================================================

    path(
        "requests/",
        views.lab_requests,
        name="lab_requests"
    ),

    path(
        "requests/create/",
        views.create_lab_request,
        name="create_lab_request"
    ),


    # =========================================================
    # LABORATORY RESULTS
    # =========================================================

    path(
        "requests/<int:request_id>/result/",
        views.enter_result,
        name="enter_result"
    ),

    path(
        "patient/<int:patient_id>/results/",
        views.patient_lab_results,
        name="patient_lab_results"
    ),

]