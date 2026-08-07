from rest_framework import serializers

from .models import Document


class DocumentSerializer(serializers.ModelSerializer):
    """Serializer for reading and writing documents."""


    file = serializers.FileField(write_only=True)
    download_url = serializers.SerializerMethodField()
    owner = serializers.ReadOnlyField(source="owner.username")

    class Meta:
        model = Document
        fields = [
            "id",
            "title",
            "file",
            "download_url",
            "owner",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "owner", "created_at", "updated_at"]

    def get_download_url(self, obj) -> str:
        return obj.presigned_url