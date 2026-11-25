
import logging

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import transaction

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from .models import (
    Notification,
    NotificationRecipient
)


logger = logging.getLogger(__name__)

User = get_user_model()


# =====================================================
# BROADCAST NOTIFICATION TO EACH RECIPIENT
# =====================================================

def broadcast_notification(notification_id, recipient_ids):
    channel_layer = get_channel_layer()

    if channel_layer is None:
        logger.error("Notification channel layer is unavailable.")
        return

    recipient_records = (
        NotificationRecipient.objects
        .filter(
            notification_id=notification_id,
            recipient_id__in=recipient_ids
        )
        .select_related("notification")
    )

    for record in recipient_records:
        notification = record.notification

        try:
            async_to_sync(channel_layer.group_send)(
                f"notifications_user_{record.recipient_id}",
                {
                    "type": "notification.message",
                    "notification": {
                        # Must be NotificationRecipient.id
                        "id": record.id,
                        "title": notification.title,
                        "message": notification.message,
                        "type": notification.notification_type,
                        "source_module": notification.source_module,
                        "reference_id": notification.reference_id,
                        "url": notification.url,
                        "created_at": notification.created_at.isoformat(),
                    }
                }
            )

        except Exception:
            logger.exception(
                "Notification broadcast failed for user %s",
                record.recipient_id
            )


# =====================================================
# CENTRAL NOTIFICATION FUNCTION
# =====================================================

def send_notification(
    title,
    message,
    notification_type,
    department=None,
    recipient=None,
    recipients=None,
    source_module="",
    reference_id=None,
    url="",
    sender=None
):
    """
    CENTRAL NOTIFICATION FUNCTION FOR THE ENTIRE HMS.

    Supports:
        - Department notifications
        - Individual user notifications
        - Multiple user notifications
        - Database storage
        - Real-time WebSocket broadcasting

    Department notifications use Django Groups.
    The department argument must match a Django Group name.
    """

    users = {}

    # =================================================
    # 1. FIND DEPARTMENT USERS
    # =================================================

    if department:

        if isinstance(department, Group):
            department_name = department.name
        else:
            department_name = str(department).strip()

        department_group = Group.objects.filter(
            name__iexact=department_name
        ).first()

        if department_group:

            department_users = User.objects.filter(
                groups=department_group,
                is_active=True
            ).distinct()

            for user in department_users:
                users[user.id] = user

        else:

            logger.warning(
                "Department group '%s' does not exist.",
                department_name
            )

    # =================================================
    # 2. ADD INDIVIDUAL USER
    # =================================================

    if recipient and recipient.is_active:
        users[recipient.id] = recipient

    # =================================================
    # 3. ADD MULTIPLE USERS
    # =================================================

    if recipients:

        for user in recipients:

            if user and user.is_active:
                users[user.id] = user

    # =================================================
    # 4. CHECK RECIPIENTS
    # =================================================

    if not users:

        logger.warning(
            "No recipients found for notification: %s",
            title
        )

        return None

    # =================================================
    # 5. SAVE NOTIFICATION AND RECIPIENT RECORDS
    # =================================================

    with transaction.atomic():

        notification = Notification.objects.create(

            title=title,

            message=message,

            notification_type=notification_type,

            source_module=source_module,

            reference_id=reference_id,

            url=url,

            sender=sender
        )

        recipient_records = [

            NotificationRecipient(
                notification=notification,
                recipient=user
            )

            for user in users.values()
        ]

        NotificationRecipient.objects.bulk_create(
            recipient_records
        )

        recipient_ids = list(users.keys())

        # =============================================
        # 6. BROADCAST ONLY AFTER DATABASE COMMIT
        # =============================================

        transaction.on_commit(

            lambda notification_id=notification.id,
                   ids=recipient_ids:

                broadcast_notification(
                    notification_id,
                    ids
                )
        )

    return notification
