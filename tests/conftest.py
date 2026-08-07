import pytest
from rest_framework.test import APIClient

from accounts.models import User


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def make_user(db):
    def _make(username, role, password="pw"):
        return User.objects.create_user(
            username=username, password=password, role=role
        )

    return _make


@pytest.fixture
def admin_user(make_user):
    return make_user("admin", User.Role.ADMIN)


@pytest.fixture
def editor_user(make_user):
    return make_user("editor", User.Role.EDITOR)


@pytest.fixture
def viewer_user(make_user):
    return make_user("viewer", User.Role.VIEWER)


@pytest.fixture
def auth_client(api_client):
    def _auth(user):
        api_client.force_authenticate(user=user)
        return api_client

    return _auth