import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from documents.ws_consumers import DOCUMENTS_GROUP

logger = logging.getLogger(__name__)


def notify_document_event(event: str, *, document_id, title, status=""):
    """
    Broadcast a document lifecycle event to all connected clients.
    """
    payload = {
        "event": event,
        "document": {"id": document_id, "title": title, "status": status},
    }

    try:
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            DOCUMENTS_GROUP,
            {"type": "document.event", "payload": payload},
        )
    except Exception:
        logger.exception("Failed to broadcast document event=%s", event)
