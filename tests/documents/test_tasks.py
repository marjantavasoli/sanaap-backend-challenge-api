import pytest

from documents.models import AuditLog, Document
from documents.tasks import process_document


@pytest.mark.django_db
def test_process_document_marks_ready(editor_user):
    document = Document.objects.create(
        owner=editor_user,
        title="report.pdf",
        file="documents/1/abc/report.pdf",
        status=Document.Status.PENDING,
    )

    process_document(document.id)

    document.refresh_from_db()
    assert document.status == Document.Status.READY


@pytest.mark.django_db
def test_process_document_missing_row_is_noop():
    # Should not raise even if the document doesn't exist.
    process_document(999999)


@pytest.mark.django_db
def test_process_document_writes_finalize_audit(editor_user):
    document = Document.objects.create(
        owner=editor_user,
        title="report.pdf",
        file="documents/1/abc/report.pdf",
        status=Document.Status.PENDING,
    )

    process_document(document.id)

    assert AuditLog.objects.filter(
        action=AuditLog.Action.CREATE, document_id=document.id
    ).exists()