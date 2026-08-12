from django.urls import path

from documents.ws_consumers import DocumentNotifyConsumer

websocket_urlpatterns = [
    path("ws/documents/", DocumentNotifyConsumer.as_asgi()),
]
