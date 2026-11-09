
from channels.generic.websocket import AsyncJsonWebsocketConsumer


class NotificationConsumer(
    AsyncJsonWebsocketConsumer
):

    async def connect(self):

        user = self.scope["user"]

        if not user.is_authenticated or not user.is_active:

            await self.close()
            return

        self.notification_group = (
            f"notifications_user_{user.id}"
        )

        await self.channel_layer.group_add(
            self.notification_group,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):

        if hasattr(self, "notification_group"):

            await self.channel_layer.group_discard(
                self.notification_group,
                self.channel_name
            )

    async def notification_message(self, event):

        await self.send_json(
            event["notification"]
        )
