import pytest

from documents.models import AuditLog, Document
from documents.services import DocumentService

service = DocumentService()


@pytest.mark.django_db
def test_handle_created_audits_with_actor(editor_user):
    document = Document.objects.create(
        owner=editor_user, title="r.pdf",
        file="documents/1/abc/r.pdf", status=Document.Status.PENDING,
    )

    service.handle_created(document, editor_user)

    log = AuditLog.objects.get(action=AuditLog.Action.CREATE)
    assert log.actor == editor_user
    assert log.document_title == "r.pdf"


@pytest.mark.django_db
def test_handle_deleted_records_without_instance(editor_user):
    # Post-deletion contract: id/title passed explicitly, no instance.
    service.handle_deleted(42, "gone.pdf", editor_user)

    log = AuditLog.objects.get(action=AuditLog.Action.DELETE)
    assert log.document_id == 42
    assert log.document_title == "gone.pdf"


@pytest.mark.django_db
def test_mark_ready_does_not_write_audit(editor_user):
    document = Document.objects.create(
        owner=editor_user, title="r.pdf",
        file="documents/1/abc/r.pdf", status=Document.Status.READY,
    )

    service.mark_ready(document)

    # No audit row: the create was already audited at the API call; "ready"
    # only notifies.
    assert AuditLog.objects.count() == 0


@pytest.mark.django_db
def test_record_list_access_audits_list(viewer_user):
    service.record_list_access(viewer_user)

    assert AuditLog.objects.filter(action=AuditLog.Action.LIST).count() == 1