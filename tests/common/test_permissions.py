import pytest
from django.contrib.auth.models import AnonymousUser
from rest_framework.test import APIRequestFactory

from accounts.models import User
from common.permissions import DocumentAccessPolicy, IsAdmin


@pytest.fixture
def factory():
    return APIRequestFactory()


class DummyView:
    """Stand-in for a real view"""


def make_user(role):
    return User(username=f"{role}-user", role=role)


@pytest.mark.parametrize(
    "role,method,expected",
    [
        # viewer: read only
        (User.Role.VIEWER, "get", True),
        (User.Role.VIEWER, "post", False),
        (User.Role.VIEWER, "put", False),
        (User.Role.VIEWER, "patch", False),
        (User.Role.VIEWER, "delete", False),
        # editor: read + write, but no delete
        (User.Role.EDITOR, "get", True),
        (User.Role.EDITOR, "post", True),
        (User.Role.EDITOR, "put", True),
        (User.Role.EDITOR, "patch", True),
        (User.Role.EDITOR, "delete", False),
        # admin: full access
        (User.Role.ADMIN, "get", True),
        (User.Role.ADMIN, "post", True),
        (User.Role.ADMIN, "put", True),
        (User.Role.ADMIN, "patch", True),
        (User.Role.ADMIN, "delete", True),
    ],
)
def test_document_access_policy(factory, role, method, expected):
    request = getattr(factory, method)("/documents/")
    request.user = make_user(role)

    assert DocumentAccessPolicy().has_permission(request, DummyView()) is expected


def test_document_access_policy_denies_anonymous(factory):
    request = factory.get("/documents/")
    request.user = AnonymousUser()

    assert DocumentAccessPolicy().has_permission(request, DummyView()) is False


@pytest.mark.parametrize(
    "role,expected",
    [
        (User.Role.ADMIN, True),
        (User.Role.EDITOR, False),
        (User.Role.VIEWER, False),
    ],
)
def test_is_admin_permission(factory, role, expected):
    request = factory.get("/")
    request.user = make_user(role)

    assert IsAdmin().has_permission(request, DummyView()) is expected