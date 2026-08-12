import pytest
from django.core.files.storage import InMemoryStorage

from documents.models import Document


class FakeDocumentStorage(InMemoryStorage):
    """In-memory storage that also fakes the presigned PUT URL, so direct-
    upload tests run without MinIO."""

    def presigned_put_url(self, name: str) -> str:
        return f"http://testserver/upload/{name}"


@pytest.fixture(autouse=True)
def in_memory_document_storage(monkeypatch):
    storage = FakeDocumentStorage(base_url="http://testserver/documents/")
    monkeypatch.setattr(Document._meta.get_field("file"), "storage", storage)
    return storage
