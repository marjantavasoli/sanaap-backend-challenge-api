import pytest
from django.urls import reverse

from documents.models import Document


@pytest.fixture
def sample_documents(editor_user):
    Document.objects.create(
        title="Alpha Report", file="documents/1/a.pdf", owner=editor_user
    )
    Document.objects.create(
        title="Beta Memo", file="documents/1/b.pdf", owner=editor_user
    )
    Document.objects.create(
        title="Gamma Report", file="documents/1/c.pdf", owner=editor_user
    )


@pytest.mark.django_db
def test_filter_by_title_is_case_insensitive_partial(
    auth_client, viewer_user, sample_documents
):
    client = auth_client(viewer_user)

    response = client.get(reverse("document-list"), {"title": "report"})

    assert response.status_code == 200
    titles = {row["title"] for row in response.data["results"]}
    assert titles == {"Alpha Report", "Gamma Report"}


@pytest.mark.django_db
def test_ordering_by_title(auth_client, viewer_user, sample_documents):
    client = auth_client(viewer_user)

    response = client.get(reverse("document-list"), {"ordering": "title"})

    titles = [row["title"] for row in response.data["results"]]
    assert titles == ["Alpha Report", "Beta Memo", "Gamma Report"]


@pytest.mark.django_db
def test_pagination_limits_page_size(auth_client, viewer_user, editor_user):
    for i in range(12):
        Document.objects.create(
            title=f"Doc {i}", file=f"documents/1/{i}.pdf", owner=editor_user
        )
    client = auth_client(viewer_user)

    response = client.get(reverse("document-list"))

    assert response.data["count"] == 12
    assert len(response.data["results"]) == 10
    assert response.data["next"] is not None