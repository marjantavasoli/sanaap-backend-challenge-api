from django.urls import reverse


def test_health_check_returns_ok(client):
    url = reverse("health-check")

    response = client.get(url)

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
