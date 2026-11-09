
from django.contrib import admin

from .models import (
    Notification,
    NotificationRecipient
)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "title",
        "notification_type",
        "source_module",
        "sender",
        "created_at",
    )

    search_fields = (
        "title",
        "message",
    )

    list_filter = (
        "notification_type",
        "source_module",
        "created_at",
    )


@admin.register(NotificationRecipient)
class NotificationRecipientAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "notification",
        "recipient",
        "is_read",
        "created_at",
    )

    list_filter = (
        "is_read",
        "created_at",
    )

    search_fields = (
        "recipient__username",
        "notification__title",
    )
