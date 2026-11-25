
from django.contrib import admin
from django.urls import path, include

from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [

    # =====================================================
    # ADMIN
    # =====================================================

    path("admin/", admin.site.urls),

    # =====================================================
    # ACCOUNTS
    # =====================================================

    path("", include("accounts.urls")),

    # =====================================================
    # PATIENTS
    # =====================================================

    path("", include("patients.urls")),

    # =====================================================
    # LABORATORY
    # =====================================================

    path("laboratory/", include("laboratory.urls")),

    # =====================================================
    # PHARMACY
    # =====================================================

    path("pharmacy/", include("pharmacy.urls")),

    # =====================================================
    # BILLING
    # =====================================================

    path("billing/", include("billing.urls")),

    # =====================================================
    # WARDS
    # =====================================================

    path("wards/", include("wards.urls")),

    # =====================================================
    # CONSULTATIONS
    # =====================================================

    path("consultations/", include("consultations.urls")),

    # =====================================================
    # NOTIFICATIONS
    # =====================================================

    path("notifications/", include("notifications.urls")),

]


# =========================================================
# DEVELOPMENT STATIC AND MEDIA FILES
# =========================================================

if settings.DEBUG:

    urlpatterns += static(
        settings.STATIC_URL,
        document_root=settings.STATIC_ROOT
    )

    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )
