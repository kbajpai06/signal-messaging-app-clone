from fastapi.testclient import TestClient

from tests.conftest import SEEDED_PHONE, auth_headers, login


def test_request_otp_ok(client: TestClient) -> None:
    res = client.post("/api/v1/auth/otp/request", json={"phone_number": "+15551230000"})
    assert res.status_code == 200
    assert res.json()["sent"] is True


def test_request_otp_normalizes_formatting(client: TestClient) -> None:
    res = client.post("/api/v1/auth/otp/request", json={"phone_number": "+1 (555) 123-0000"})
    assert res.status_code == 200


def test_request_otp_rejects_invalid_phone(client: TestClient) -> None:
    res = client.post("/api/v1/auth/otp/request", json={"phone_number": "12345"})
    assert res.status_code == 422
    assert res.json()["error"]["code"] == "validation_error"


def test_verify_with_wrong_code_is_unauthorized(client: TestClient) -> None:
    res = client.post(
        "/api/v1/auth/otp/verify", json={"phone_number": "+15551230000", "code": "000000"}
    )
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "invalid_otp"


def test_verify_creates_user_then_logs_in_existing(client: TestClient) -> None:
    first = login(client)
    second = login(client)
    assert first["is_new_user"] is True
    assert second["is_new_user"] is False
    assert first["user"]["id"] == second["user"]["id"]
    assert first["token"] != second["token"]  # separate sessions


def test_me_requires_token(client: TestClient) -> None:
    res = client.get("/api/v1/auth/me")
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "missing_token"


def test_me_with_token(client: TestClient) -> None:
    data = login(client)
    res = client.get("/api/v1/auth/me", headers=auth_headers(data["token"]))
    assert res.status_code == 200
    assert res.json()["id"] == data["user"]["id"]


def test_tampered_token_is_rejected(client: TestClient) -> None:
    data = login(client)
    res = client.get("/api/v1/auth/me", headers=auth_headers(data["token"] + "x"))
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "invalid_token"


def test_logout_revokes_only_that_session(client: TestClient) -> None:
    first = login(client)
    second = login(client)

    res = client.post("/api/v1/auth/logout", headers=auth_headers(first["token"]))
    assert res.status_code == 204

    revoked = client.get("/api/v1/auth/me", headers=auth_headers(first["token"]))
    assert revoked.status_code == 401
    assert revoked.json()["error"]["code"] == "session_invalid"

    still_ok = client.get("/api/v1/auth/me", headers=auth_headers(second["token"]))
    assert still_ok.status_code == 200


def test_seeded_user_can_log_in(seeded_client: TestClient) -> None:
    data = login(seeded_client, SEEDED_PHONE)
    assert data["is_new_user"] is False
    assert data["user"]["display_name"] == "Alice Johnson"
