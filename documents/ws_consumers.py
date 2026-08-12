from channels.generic.websocket import AsyncJsonWebsocketConsumer

# All authenticated clients join this single group; document events are
# broadcast to everyone (documents are a shared collection).
DOCUMENTS_GROUP = "documents"


class DocumentNotifyConsumer(AsyncJsonWebsocketConsumer):
    """
    Pushes document lifecycle events (created/updated/ready/deleted) to connected, authenticated clients.
    """

    async def connect(self):
        user = self.scope.get("user")
        if user is None or not user.is_authenticated:
            await self.close(code=4401)  # unauthorized
            return

        await self.channel_layer.group_add(DOCUMENTS_GROUP, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(DOCUMENTS_GROUP, self.channel_name)

    async def document_event(self, event):
        await self.send_json(event["payload"])