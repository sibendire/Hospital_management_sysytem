
from django.conf import settings
from django.db import models


class Notification(models.Model):

    title = models.CharField(
        max_length=200
    )

    message = models.TextField()

    notification_type = models.CharField(
        max_length=100
    )

    source_module = models.CharField(
        max_length=100,
        blank=True
    )

    reference_id = models.PositiveIntegerField(
        null=True,
        blank=True
    )

    url = models.CharField(
        max_length=500,
        blank=True
    )

    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sent_hms_notifications"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class NotificationRecipient(models.Model):

    notification = models.ForeignKey(
        Notification,
        on_delete=models.CASCADE,
        related_name="recipients"
    )

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="hms_notifications"
    )

    is_read = models.BooleanField(
        default=False
    )

    read_at = models.DateTimeField(
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:

        ordering = ["-created_at"]

        constraints = [
            models.UniqueConstraint(
                fields=["notification", "recipient"],
                name="unique_notification_recipient"
            )
        ]

        indexes = [
            models.Index(
                fields=[
                    "recipient",
                    "is_read",
                    "-created_at"
                ]
            )
        ]

    def __str__(self):

        return (
            f"{self.notification.title} - "
            f"{self.recipient.username}"
        )
