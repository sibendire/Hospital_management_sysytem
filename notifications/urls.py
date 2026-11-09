
from django.urls import path

from . import views


app_name = "notifications"


urlpatterns = [

    path(
        "",
        views.notification_feed,
        name="notification_feed"
    ),

    path(
        "mark-read/<int:notification_id>/",
        views.mark_notification_read,
        name="mark_notification_read"
    ),

    path(
        "mark-all-read/",
        views.mark_all_notifications_read,
        name="mark_all_read"
    ),

]
