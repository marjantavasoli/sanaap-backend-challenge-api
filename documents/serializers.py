import uuid

from rest_framework import serializers

from documents.models import AuditLog, Document, build_document_key


class DocumentSerializer(serializers.ModelSerializer):
    """Read + create serializer for documents.

    On create the client sends only ``title``; the response includes a
    presigned ``upload_url`` the client PUTs the file to. ``file`` is never
    uploaded through Django.
    """

    download_url = serializers.SerializerMethodField()
    upload_url = serializers.SerializerMethodField()
    owner = serializers.ReadOnlyField(source="owner.username")

    class Meta:
        model = Document
        fields = [
            "id",
            "title",
            "status",
            "size",
            "content_type",
            "download_url",
            "upload_url",
            "owner",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "status",
            "size",
            "content_type",
            "owner",
            "created_at",
            "updated_at",
        ]

    def get_download_url(self, obj) -> str:
        # Only meaningful once the object exists (ready).
        return obj.presigned_url if obj.status == Document.Status.READY else ""

    def get_upload_url(self, obj) -> str:
        # Populated by the view immediately after create; not stored.
        return getattr(obj, "_upload_url", "")

    def create(self, validated_data):
        owner = self.context["request"].user
        # Namespace the key by owner so the webhook can recover ownership,
        # and add a uuid so keys are unique and unguessable.
        filename = validated_data["title"]
        key = build_document_key(owner.id, filename)

        document = Document.objects.create(
            owner=owner,
            title=validated_data["title"],
            file=key,
            status=Document.Status.PENDING,
        )
        # Attach the presigned PUT URL for the response (not persisted).
        document._upload_url = document.file.storage.presigned_put_url(key)
        return document


class AuditLogSerializer(serializers.ModelSerializer):
    actor = serializers.ReadOnlyField(source="actor.username")

    class Meta:
        model = AuditLog
        fields = [
            "id",
            "actor",
            "action",
            "document_id",
            "document_title",
            "created_at",
        ]
