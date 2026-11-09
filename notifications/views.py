
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from .models import NotificationRecipient


@login_required
@require_GET
def notification_feed(request):

    notifications = (

        NotificationRecipient.objects

        .filter(
            recipient=request.user
        )

        .select_related(
            "notification"
        )

        .order_by("-created_at")[:30]

    )

    unread_count = (

        NotificationRecipient.objects

        .filter(
            recipient=request.user,
            is_read=False
        )

        .count()

    )

    data = []

    for item in notifications:

        notification = item.notification

        data.append({

            "id": item.id,

            "title": notification.title,

            "message": notification.message,

            "type": notification.notification_type,

            "source_module": notification.source_module,

            "reference_id": notification.reference_id,

            "url": notification.url,

            "is_read": item.is_read,

            "created_at": item.created_at.isoformat(),

        })

    return JsonResponse({

        "notifications": data,

        "unread_count": unread_count,

    })


@login_required
@require_POST
def mark_notification_read(request, notification_id):

    notification = get_object_or_404(

        NotificationRecipient,

        id=notification_id,

        recipient=request.user

    )

    if not notification.is_read:

        notification.is_read = True

        notification.read_at = timezone.now()

        notification.save(
            update_fields=[
                "is_read",
                "read_at"
            ]
        )

    return JsonResponse({

        "success": True,

        "message": "Notification marked as read."

    })


@login_required
@require_POST
def mark_all_notifications_read(request):

    NotificationRecipient.objects.filter(

        recipient=request.user,

        is_read=False

    ).update(

        is_read=True,

        read_at=timezone.now()

    )

    return JsonResponse({

        "success": True,

        "message": "All notifications marked as read."

    })
