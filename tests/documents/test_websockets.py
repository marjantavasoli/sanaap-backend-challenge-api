import pytest
from channels.db import database_sync_to_async
from channels.routing import URLRouter
from channels.testing import WebsocketCommunicator
from rest_framework_simplejwt.tokens import AccessToken

from accounts.models import User
from common.websocket_authentication import JWTWebsocketAuthenticationMiddleware
from documents.ws_notifications import notify_document_event
from documents.ws_routing import websocket_urlpatterns

# Build the same middleware stack the ASGI app uses, so tests exercise auth.
application = JWTWebsocketAuthenticationMiddleware(URLRouter(websocket_urlpatterns))


def token_for(user):
    return str(AccessToken.for_user(user))


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_authenticated_client_receives_document_event(settings):
    settings.CHANNEL_LAYERS = {"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}
    user = await _make_user()
    communicator = WebsocketCommunicator(application, f"/ws/documents/?token={token_for(user)}")
    connected, _ = await communicator.connect()
    assert connected

    # Broadcast an event and confirm the socket receives it.
    from asgiref.sync import sync_to_async

    await sync_to_async(notify_document_event)(
        "ready", document_id=1, title="report.pdf", status="ready"
    )

    message = await communicator.receive_json_from(timeout=2)
    assert message["event"] == "ready"
    assert message["document"]["id"] == 1
    await communicator.disconnect()


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_unauthenticated_client_is_rejected(settings):
    settings.CHANNEL_LAYERS = {"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}
    communicator = WebsocketCommunicator(application, "/ws/documents/")  # no token

    connected, _ = await communicator.connect()
    assert connected is False

    await communicator.disconnect()


@database_sync_to_async
def _make_user():
    return User.objects.create_user(username="ws-user", password="pw")
