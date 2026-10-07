from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app

SEEDED_PHONE = "+15550000001"  # Alice


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(
        _env_file=None,
        env="test",
        secret_key="test-secret-key-0123456789-abcdefghijklmnop",
        database_url=f"sqlite+aiosqlite:///{tmp_path / 'test.db'}",
        seed_on_startup=False,
    )


@pytest.fixture
def client(settings: Settings) -> Iterator[TestClient]:
    with TestClient(create_app(settings)) as test_client:
        yield test_client


@pytest.fixture
def seeded_client(settings: Settings) -> Iterator[TestClient]:
    seeded = settings.model_copy(update={"seed_on_startup": True})
    with TestClient(create_app(seeded)) as test_client:
        yield test_client


def login(client: TestClient, phone: str = "+15551230000") -> dict:
    response = client.post(
        "/api/v1/auth/otp/verify", json={"phone_number": phone, "code": "123456"}
    )
    assert response.status_code == 200, response.text
    return response.json()


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}
