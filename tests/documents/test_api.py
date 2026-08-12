import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from documents.models import Document


def make_upload(name="report.pdf", content=b"data"):
    return SimpleUploadedFile(name, content, content_type="application/pdf")


@pytest.mark.django_db
def test_editor_create_returns_pending_and_upload_url(auth_client, editor_user):
    client = auth_client(editor_user)

    response = client.post(
        reverse("document-list"),
        {"title": "Q4 Report"},
        format="json",
    )

    assert response.status_code == 201
    assert response.data["status"] == "pending"
    assert response.data["upload_url"].startswith("http://")
    assert response.data["download_url"] == ""
    document = Document.objects.get(id=response.data["id"])
    assert document.owner == editor_user


@pytest.mark.django_db
def test_owner_is_taken_from_request_not_payload(auth_client, editor_user, admin_user):
    client = auth_client(editor_user)
    response = client.post(
        reverse("document-list"),
        {"title": "X", "owner": admin_user.id},  # try to forge owner
        format="json",
    )
    assert response.status_code == 201
    assert Document.objects.get().owner == editor_user


@pytest.mark.django_db
def test_viewer_can_list_documents(auth_client, viewer_user, editor_user):
    Document.objects.create(title="Doc", file="documents/1/a.pdf", owner=editor_user)
    client = auth_client(viewer_user)

    response = client.get(reverse("document-list"))

    assert response.status_code == 200
    assert response.data["count"] == 1


@pytest.mark.django_db
def test_viewer_cannot_create_document(auth_client, viewer_user):
    client = auth_client(viewer_user)

    response = client.post(reverse("document-list"), {"title": "Nope"}, format="json")

    assert response.status_code == 403
    assert Document.objects.count() == 0


@pytest.mark.django_db
def test_editor_can_update_document_title(auth_client, editor_user):
    document = Document.objects.create(title="Old", file="documents/1/a.pdf", owner=editor_user)
    client = auth_client(editor_user)

    response = client.patch(
        reverse("document-detail", args=[document.id]),
        {"title": "New"},
        format="multipart",
    )

    assert response.status_code == 200
    document.refresh_from_db()
    assert document.title == "New"


@pytest.mark.django_db
def test_editor_cannot_delete_document(auth_client, editor_user):
    document = Document.objects.create(title="Doc", file="documents/1/a.pdf", owner=editor_user)
    client = auth_client(editor_user)

    response = client.delete(reverse("document-detail", args=[document.id]))

    assert response.status_code == 403
    assert Document.objects.filter(id=document.id).exists()


@pytest.mark.django_db
def test_admin_can_delete_document(auth_client, admin_user):
    document = Document.objects.create(
        owner=admin_user,
        title="Doc",
        file="documents/1/abc/doc.pdf",
        status=Document.Status.READY,
    )
    client = auth_client(admin_user)
    response = client.delete(reverse("document-detail", args=[document.id]))
    assert response.status_code == 204
    assert Document.objects.count() == 0


@pytest.mark.django_db
def test_unauthenticated_request_is_rejected(api_client):
    response = api_client.get(reverse("document-list"))

    assert response.status_code == 401
