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
def test_process_document_does_not_write_audit(editor_user):
    document = Document.objects.create(
        owner=editor_user,
        title="report.pdf",
        file="documents/1/abc/report.pdf",
        status=Document.Status.PENDING,
    )

    process_document(document.id)

    # Processing finalizes + notifies but writes NO audit row — the create
    # was already audited at the API call.
    assert AuditLog.objects.count() == 0
