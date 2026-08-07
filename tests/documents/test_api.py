import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from documents.models import Document


def make_upload(name="report.pdf", content=b"data"):
    return SimpleUploadedFile(name, content, content_type="application/pdf")


@pytest.mark.django_db
def test_editor_can_upload_document(auth_client, editor_user):
    client = auth_client(editor_user)

    response = client.post(
        reverse("document-list"),
        {"title": "Marjan Report", "file": make_upload()},
        format="multipart",
    )

    assert response.status_code == 201
    assert Document.objects.count() == 1
    document = Document.objects.get()
    assert document.owner == editor_user
    assert document.title == "Marjan Report"
    assert response.data["download_url"].startswith("http://testserver/documents/")


@pytest.mark.django_db
def test_owner_is_taken_from_request_not_payload(auth_client, editor_user, admin_user):
    client = auth_client(editor_user)
    response = client.post(
        reverse("document-list"),
        {"title": "X", "file": make_upload(), "owner": admin_user.id},
        format="multipart",
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
def test_viewer_cannot_upload_document(auth_client, viewer_user):
    client = auth_client(viewer_user)

    response = client.post(
        reverse("document-list"),
        {"title": "Nope", "file": make_upload()},
        format="multipart",
    )

    assert response.status_code == 403
    assert Document.objects.count() == 0


@pytest.mark.django_db
def test_editor_can_update_document_title(auth_client, editor_user):
    document = Document.objects.create(
        title="Old", file="documents/1/a.pdf", owner=editor_user
    )
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
    document = Document.objects.create(
        title="Doc", file="documents/1/a.pdf", owner=editor_user
    )
    client = auth_client(editor_user)

    response = client.delete(reverse("document-detail", args=[document.id]))

    assert response.status_code == 403
    assert Document.objects.filter(id=document.id).exists()


@pytest.mark.django_db
def test_admin_can_delete_document(auth_client, admin_user):
    client = auth_client(admin_user)
    created = client.post(
        reverse("document-list"),
        {"title": "Doc", "file": make_upload()},
        format="multipart",
    )
    document_id = created.data["id"]

    response = client.delete(reverse("document-detail", args=[document_id]))

    assert response.status_code == 204
    assert Document.objects.count() == 0


@pytest.mark.django_db
def test_unauthenticated_request_is_rejected(api_client):
    response = api_client.get(reverse("document-list"))

    assert response.status_code == 401