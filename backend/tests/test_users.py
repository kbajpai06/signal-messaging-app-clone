from fastapi.testclient import TestClient

from tests.conftest import auth_headers, login

URL = "/api/v1/users/me"


def test_update_profile(client: TestClient) -> None:
    token = login(client)["token"]
    res = client.put(
        URL,
        headers=auth_headers(token),
        json={"display_name": "  Zed  ", "about": "Hello", "username": "Zed.42"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["display_name"] == "Zed"
    assert body["about"] == "Hello"
    assert body["username"] == "zed.42"


def test_partial_update_leaves_other_fields(client: TestClient) -> None:
    token = login(client)["token"]
    client.put(URL, headers=auth_headers(token), json={"about": "Hi", "display_name": "Zed"})
    res = client.put(URL, headers=auth_headers(token), json={"about": ""})
    assert res.status_code == 200
    assert res.json()["about"] is None
    assert res.json()["display_name"] == "Zed"


def test_display_name_cannot_be_null(client: TestClient) -> None:
    token = login(client)["token"]
    res = client.put(URL, headers=auth_headers(token), json={"display_name": None})
    assert res.status_code == 422


def test_username_conflict(client: TestClient) -> None:
    first = login(client, "+15551230001")["token"]
    second = login(client, "+15551230002")["token"]
    response = client.put(URL, headers=auth_headers(first), json={"username": "taken.01"})
    assert response.status_code == 200

    res = client.put(URL, headers=auth_headers(second), json={"username": "taken.01"})
    assert res.status_code == 409
    assert res.json()["error"]["code"] == "username_taken"


def test_update_requires_auth(client: TestClient) -> None:
    assert client.put(URL, json={"about": "x"}).status_code == 401
