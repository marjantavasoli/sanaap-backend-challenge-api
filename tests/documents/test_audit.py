import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from documents.models import AuditLog, Document


def make_upload(name="report.pdf", content=b"data"):
    return SimpleUploadedFile(name, content, content_type="application/pdf")


@pytest.mark.django_db
def test_upload_creates_audit_log(auth_client, editor_user):
    client = auth_client(editor_user)

    client.post(
        reverse("document-list"),
        {"title": "Q4", "file": make_upload()},
        format="json",
    )

    log = AuditLog.objects.get(action=AuditLog.Action.CREATE)
    assert log.actor == editor_user
    assert log.document_title == "Q4"


@pytest.mark.django_db
def test_list_creates_access_log(auth_client, viewer_user):
    client = auth_client(viewer_user)

    client.get(reverse("document-list"))

    assert AuditLog.objects.filter(action=AuditLog.Action.LIST).count() == 1


@pytest.mark.django_db
def test_delete_log_survives_document_deletion(auth_client, admin_user):
    client = auth_client(admin_user)
    created = client.post(
        reverse("document-list"),
        {"title": "Doomed", "file": make_upload()},
        format="multipart",
    )
    document_id = created.data["id"]

    client.delete(reverse("document-detail", args=[document_id]))

    # The document is gone, but its delete log remains with a readable title.
    assert not Document.objects.filter(id=document_id).exists()
    delete_log = AuditLog.objects.get(action=AuditLog.Action.DELETE)
    assert delete_log.document_id == document_id
    assert delete_log.document_title == "Doomed"


@pytest.mark.django_db
def test_denied_action_is_not_logged(auth_client, viewer_user):
    client = auth_client(viewer_user)

    # Viewer can't upload -> 403, and nothing should be recorded.
    response = client.post(
        reverse("document-list"),
        {"title": "Nope", "file": make_upload()},
        format="multipart",
    )

    assert response.status_code == 403
    assert AuditLog.objects.filter(action=AuditLog.Action.CREATE).count() == 0


@pytest.mark.django_db
def test_only_admin_can_read_audit_logs(auth_client, admin_user, viewer_user):
    # Generate a log entry.
    auth_client(viewer_user).get(reverse("document-list"))

    # Viewer is forbidden.
    viewer_resp = auth_client(viewer_user).get(reverse("audit-log-list"))
    assert viewer_resp.status_code == 403

    # Admin can read.
    admin_resp = auth_client(admin_user).get(reverse("audit-log-list"))
    assert admin_resp.status_code == 200
    assert admin_resp.data["count"] >= 1


@pytest.mark.django_db
def test_service_normalizes_anonymous_actor():
    from django.contrib.auth.models import AnonymousUser
    from documents.services import DocumentService

    DocumentService().record_list_access(AnonymousUser())

    log = AuditLog.objects.get(action=AuditLog.Action.LIST)
    assert log.actor is None