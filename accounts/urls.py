from django.urls import path

from .views import (
    signup_view,
    login_view,
    logout_view,
    # add_patient_view,
    dashboard
)


urlpatterns = [

    path(
        'signup/',
        signup_view,
        name='signup'
    ),
    # path(
    #     'Add_Patient/', 
    #      add_patient_view,
    #      name='Add_Patient'
    # ),

    path(
        'login/',
        login_view,
        name='login'
    ),

    path(
        'logout/',
        logout_view,
        name='logout'
    ),

    path(
        'dashboard/',
        dashboard,
        name='dashboard'
    ),

]