from rest_framework.permissions import SAFE_METHODS, BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView


class IsAdmin(BasePermission):
    def has_permission(self, request: Request, view: APIView) -> bool:
        user = request.user
        return bool(user and user.is_authenticated and (user.is_superuser or user.is_admin))


class DocumentAccessPolicy(BasePermission):
    def has_permission(self, request: Request, view: APIView) -> bool:
        user = request.user
        if user.is_superuser:
            return True

        if not (user and user.is_authenticated):
            return False

        if request.method in SAFE_METHODS:
            return True

        if request.method == "DELETE":
            return user.is_admin

        # POST, PUT, PATCH
        return user.is_editor or user.is_admin