from django.test import override_settings

from documents.storages import DocumentStorage

STORAGE_SETTINGS = dict(
    MINIO_ENDPOINT="minio:9000",
    MINIO_ACCESS_KEY="test-access",
    MINIO_SECRET_KEY="test-secret",
    MINIO_BUCKET="test-documents",
    MINIO_USE_SSL=False,
    DOCUMENT_URL_EXPIRY=120,
)


@override_settings(**STORAGE_SETTINGS)
def test_storage_is_private_and_signed():
    storage = DocumentStorage()

    assert storage.bucket_name == "test-documents"
    assert storage.default_acl == "private"
    assert storage.querystring_auth is True
    assert storage.querystring_expire == 120
    assert storage.file_overwrite is False


@override_settings(**STORAGE_SETTINGS)
def test_url_is_presigned_with_expiry():
    storage = DocumentStorage()

    url = storage.url("documents/1/example.png")

    assert url.startswith("http://minio:9000/test-documents/")
    assert "X-Amz-Signature=" in url
    assert "X-Amz-Expires=120" in url