import logging
from urllib.parse import unquote

from django.conf import settings
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from documents.models import Document
from documents.tasks import process_document

logger = logging.getLogger(__name__)

@extend_schema(exclude=True)
@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def minio_upload_hook(request: Request) -> Response:
    """Receive MinIO ObjectCreated events and enqueue processing."""
    auth = request.headers.get("Authorization", "")
    provided = auth.removeprefix("Bearer ").strip()
    if not settings.MINIO_WEBHOOK_KEY or provided != settings.MINIO_WEBHOOK_KEY:
        return Response(status=status.HTTP_401_UNAUTHORIZED)

    # MinIO S3 event: records[].s3.object.key identifies the uploaded object.
    records = request.data.get("Records", [])
    enqueued = 0
    for record in records:
        try:
            key = unquote(record["s3"]["object"]["key"])
        except (KeyError, TypeError):
            continue

        # Match the pending document by its stored key, then process it.
        document = Document.objects.filter(file=key).first()
        if document is not None:
            process_document.delay(document.id)
            enqueued += 1

    return Response({"enqueued": enqueued}, status=status.HTTP_200_OK)
