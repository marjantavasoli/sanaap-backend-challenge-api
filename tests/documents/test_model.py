import pytest

from accounts.models import User
from documents.models import Document, document_upload_path


@pytest.mark.django_db
def test_document_str_returns_title():
    owner = User.objects.create_user(username="alice", password="pw")
    document = Document.objects.create(
        title="Report1",
        file="documents/1/report.pdf",
        owner=owner,
    )

    assert str(document) == "Report1"


@pytest.mark.django_db
def test_document_is_linked_to_owner():
    owner = User.objects.create_user(username="alice", password="pw")
    document = Document.objects.create(
        title="Report", file="documents/1/report.pdf", owner=owner
    )

    assert document.owner == owner
    assert list(owner.documents.all()) == [document]


def test_upload_path_is_namespaced_per_owner():
    class DummyInstance:
        owner_id = 42

    assert document_upload_path(DummyInstance(), "photo.png") == "documents/42/photo.png"