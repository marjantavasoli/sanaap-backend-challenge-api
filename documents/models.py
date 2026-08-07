from django.conf import settings
from django.db import models

from .storages import get_document_storage


def document_upload_path(instance, filename: str) -> str:
    """Namespace stored objects per owner to keep the bucket organized."""
    return f"documents/{instance.owner_id}/{filename}"


class Document(models.Model):
    title = models.CharField(max_length=255)
    file = models.FileField(
        storage=get_document_storage,
        upload_to=document_upload_path,
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="documents",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.title

    @property
    def presigned_url(self) -> str:
        """Short-lived signed URL for downloading this document."""
        return self.file.url