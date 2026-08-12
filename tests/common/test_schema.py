import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_openapi_schema_is_served(client):
    response = client.get(reverse("schema"))

    assert response.status_code == 200
    # Spectacular serves YAML by default; assert it's the right document.
    assert b"openapi" in response.content


@pytest.mark.django_db
def test_swagger_ui_is_served(client):
    response = client.get(reverse("swagger-ui"))

    assert response.status_code == 200


@pytest.mark.django_db
def test_document_endpoint_present_in_schema(client):
    response = client.get(reverse("schema"), {"format": "json"})

    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/api/documents/" in paths
