from django.urls import path
from . import views

app_name = "wards"

urlpatterns = [
    path(
        "",
        views.ward_dashboard,
        name="dashboard"
    ),
]