from django.conf import settings
from storages.backends.s3 import S3Storage


class DocumentStorage(S3Storage):
    """Private MinIO/S3 storage for user documents."""

    def __init__(self, **kwargs):
        scheme = "https" if settings.MINIO_USE_SSL else "http"

        kwargs.setdefault("bucket_name", settings.MINIO_BUCKET)
        kwargs.setdefault("endpoint_url", f"{scheme}://{settings.MINIO_ENDPOINT}")
        kwargs.setdefault("access_key", settings.MINIO_ACCESS_KEY)
        kwargs.setdefault("secret_key", settings.MINIO_SECRET_KEY)
        kwargs.setdefault("region_name", "us-east-1")

        # MinIO requires path-style addressing (host/bucket/key), and SigV4
        # so url() produces X-Amz-* presigned links deterministically.
        kwargs.setdefault("addressing_style", "path")
        kwargs.setdefault("signature_version", "s3v4")

        # Keep objects private and hand out time-limited signed URLs.
        kwargs.setdefault("default_acl", "private")
        kwargs.setdefault("querystring_auth", True)
        kwargs.setdefault("querystring_expire", settings.DOCUMENT_URL_EXPIRY)

        # Never silently overwrite an existing object with the same name.
        kwargs.setdefault("file_overwrite", False)

        super().__init__(**kwargs)


    def presigned_put_url(self, name: str) -> str:
        """Return a presigned PUT URL the client uses to upload directly.        """


        return self.connection.meta.client.generate_presigned_url(
            "put_object",
            Params={"Bucket": self.bucket_name, "Key": name},
            ExpiresIn=settings.DOCUMENT_URL_EXPIRY,
        )

# A single shared instance. The model's FileField references it through the
# callable below so the storage config is never baked into a migration.
document_storage = DocumentStorage()


def get_document_storage():
    return document_storage