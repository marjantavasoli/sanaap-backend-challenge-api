import django_filters

from documents.models import Document


class DocumentFilter(django_filters.FilterSet):
    """Query-string filtering for documents."""

    title = django_filters.CharFilter(lookup_expr="icontains")
    created_after = django_filters.DateTimeFilter(field_name="created_at", lookup_expr="gte")
    created_before = django_filters.DateTimeFilter(field_name="created_at", lookup_expr="lte")

    class Meta:
        model = Document
        fields = ["title", "created_after", "created_before"]
