import pytest
from django.urls import reverse

from accounts.models import User


@pytest.mark.django_db
def test_obtain_jwt_token_with_valid_credentials(client):
    User.objects.create_user(username="alice", password="s3cret-pw")

    response = client.post(
        reverse("token-obtain-pair"),
        data={"username": "alice", "password": "s3cret-pw"},
        content_type="application/json",
    )

    assert response.status_code == 200
    body = response.json()
    assert "access" in body
    assert "refresh" in body


@pytest.mark.django_db
def test_obtain_jwt_token_rejects_bad_credentials(client):
    User.objects.create_user(username="alice", password="s3cret-pw")

    response = client.post(
        reverse("token-obtain-pair"),
        data={"username": "alice", "password": "wrong-pw"},
        content_type="application/json",
    )

    assert response.status_code == 401


@pytest.mark.django_db
def test_refresh_token_returns_new_access_token(client):
    User.objects.create_user(username="alice", password="s3cret-pw")
    tokens = client.post(
        reverse("token-obtain-pair"),
        data={"username": "alice", "password": "s3cret-pw"},
        content_type="application/json",
    ).json()

    response = client.post(
        reverse("token-refresh"),
        data={"refresh": tokens["refresh"]},
        content_type="application/json",
    )

    assert response.status_code == 200
    assert "access" in response.json()
