import pytest
from django.core.files.storage import InMemoryStorage

from documents.models import Document


@pytest.fixture(autouse=True)
def in_memory_document_storage(monkeypatch):
    """Swap the document FileField's storage for an in-memory backend so API
    tests exercise real uploads and downloads without a running MinIO."""
    storage = InMemoryStorage(base_url="http://testserver/documents/")
    monkeypatch.setattr(Document._meta.get_field("file"), "storage", storage)
    return storage