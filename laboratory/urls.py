from django.urls import path

from . import views



urlpatterns=[


path(
"dashboard/",
views.laboratory_dashboard,
name="laboratory_dashboard"
),



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
"requests/",
views.lab_requests,
name="lab_requests"
),



path(
"request/add/",
views.create_lab_request,
name="create_lab_request"
),



path(
"result/<int:id>/",
views.enter_result,
name="enter_result"
),


]