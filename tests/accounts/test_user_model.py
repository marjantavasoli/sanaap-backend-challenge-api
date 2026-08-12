import pytest

from accounts.models import User


@pytest.mark.django_db
def test_new_user_defaults_to_viewer_role():
    user = User.objects.create_user(username="alice", password="pw")

    assert user.role == User.Role.VIEWER
    assert user.is_viewer
    assert not user.is_editor
    assert not user.is_admin


@pytest.mark.django_db
def test_role_properties_are_mutually_exclusive():
    editor = User.objects.create_user(username="bob", password="pw", role=User.Role.EDITOR)

    assert editor.is_editor
    assert not editor.is_admin
    assert not editor.is_viewer
