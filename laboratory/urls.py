from django.urls import path

from . import views


urlpatterns = [

    # =========================================================
    # LABORATORY DASHBOARD
    # =========================================================

    path(
        "dashboard/",
        views.laboratory_dashboard,
        name="laboratory_dashboard"
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
        "tests/edit/<int:id>/",
        views.edit_test,
        name="edit_test"
    ),

    path(
        "tests/delete/<int:id>/",
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

    # Backward-compatible name for existing templates
    path(
        "requests/",
        views.lab_requests,
        name="lab_request_list"
    ),

    path(
        "request/add/",
        views.create_lab_request,
        name="create_lab_request"
    ),

    # Backward-compatible name for existing templates
    path(
        "request/add/",
        views.create_lab_request,
        name="lab_request"
    ),


    # =========================================================
    # LABORATORY RESULTS
    # =========================================================

    path(
        "result/<int:id>/",
        views.enter_result,
        name="enter_result"
    ),
]