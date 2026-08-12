from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken

User = get_user_model()


@database_sync_to_async
def _get_user(user_id):
    try:
        return User.objects.get(id=user_id)
    except User.DoesNotExist:
        return AnonymousUser()


class JWTWebsocketAuthenticationMiddleware(BaseMiddleware):
    """
    Authenticate a WebSocket connection from a ?token=<access> query param.
    """

    async def __call__(self, scope, receive, send):
        scope["user"] = AnonymousUser()
        query = parse_qs(scope.get("query_string", b"").decode())
        tokens = query.get("token")
        token = tokens[0] if tokens else None

        if token:
            try:
                access = AccessToken(token)
                scope["user"] = await _get_user(access["user_id"])
            except (TokenError, KeyError):
                scope["user"] = AnonymousUser()

        return await super().__call__(scope, receive, send)
