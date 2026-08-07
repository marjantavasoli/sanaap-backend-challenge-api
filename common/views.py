from drf_spectacular.utils import extend_schema
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response


@extend_schema(
    responses={200: {"type": "object", "properties": {"status": {"type": "string"}}}},
    description="Liveness probe. Returns `{\"status\": \"ok\"}` when the service is up.",
)
@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request: Request) -> Response:
    return Response({"status": "ok"})