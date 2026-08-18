import pytest
from django.test import override_settings
from django.urls import reverse

from documents.models import Document

WEBHOOK_KEY = "test-webhook-key"


def s3_event(key):
    return {"Records": [{"s3": {"object": {"key": key}}}]}


@pytest.mark.django_db
@override_settings(MINIO_WEBHOOK_KEY=WEBHOOK_KEY)
def test_webhook_enqueues_and_marks_ready(api_client, editor_user):
    # CELERY_TASK_ALWAYS_EAGER is on in tests, so .delay runs inline.
    document = Document.objects.create(
        owner=editor_user,
        title="r.pdf",
        file="documents/1/abc/r.pdf",
        status=Document.Status.PENDING,
    )

    response = api_client.post(
        reverse("minio-upload-hook"),
        data=s3_event("documents/1/abc/r.pdf"),
        format="json",
        HTTP_Authorization=f'Bearer {WEBHOOK_KEY}'
    )

    assert response.status_code == 200
    assert response.data["enqueued"] == 1
    document.refresh_from_db()
    assert document.status == Document.Status.READY


@pytest.mark.django_db
@override_settings(MINIO_WEBHOOK_KEY=WEBHOOK_KEY)
def test_webhook_rejects_bad_key(api_client):
    response = api_client.post(
        reverse("minio-upload-hook"),
        data=s3_event("documents/1/abc/r.pdf"),
        format="json",
        HTTP_Authorization='Bearer wrong-key'
    )

    assert response.status_code == 401


@pytest.mark.django_db
@override_settings(MINIO_WEBHOOK_KEY=WEBHOOK_KEY)
def test_webhook_unknown_key_enqueues_nothing(api_client):
    response = api_client.post(
        reverse("minio-upload-hook"),
        data=s3_event("documents/1/abc/missing.pdf"),
        format="json",
        HTTP_Authorization=f'Bearer {WEBHOOK_KEY}'
    )

    assert response.status_code == 200
    assert response.data["enqueued"] == 0
