import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def client(settings):
    with TestClient(create_app(settings)) as client:
        yield client


def authenticate(client, email):
    credentials = {"email": email, "password": "Senha-segura-123"}
    assert client.post("/api/v1/auth/register", json=credentials).status_code == 201
    response = client.post("/api/v1/auth/login", json=credentials)
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_crud_and_user_isolation(client):
    owner = authenticate(client, "owner@example.com")
    other = authenticate(client, "other@example.com")
    response = client.post(
        "/api/v1/tasks",
        headers=owner,
        json={"titulo": "  Revisar API  ", "descricao": "Detalhes"},
    )
    assert response.status_code == 201
    task = response.json()
    assert task["titulo"] == "Revisar API"
    assert task["status"] == "pending"
    assert task["data_criacao"].endswith("Z")
    path = f"/api/v1/tasks/{task['id']}"
    assert client.get(path, headers=owner).json() == task
    assert client.get("/api/v1/tasks", headers=other).json() == []
    for method, kwargs in [
        ("get", {}),
        ("patch", {"json": {"titulo": "Invadida"}}),
        ("delete", {}),
    ]:
        assert getattr(client, method)(path, headers=other, **kwargs).status_code == 404
    updated = client.patch(path, headers=owner, json={"status": "completed"})
    assert updated.status_code == 200
    assert updated.json()["descricao"] == "Detalhes"
    assert updated.json()["status"] == "completed"
    assert client.delete(path, headers=owner).status_code == 204
    assert client.get(path, headers=owner).status_code == 404


def test_filters_are_literal_and_order_is_deterministic(client):
    headers = authenticate(client, "filter@example.com")
    tasks = [
        {"titulo": "API 100%_pronta", "status": "completed"},
        {"titulo": "API 100xxpronta"},
        {"titulo": "Outra"},
    ]
    ids = [
        client.post("/api/v1/tasks", headers=headers, json=task).json()["id"]
        for task in tasks
    ]
    assert [
        task["id"] for task in client.get("/api/v1/tasks", headers=headers).json()
    ] == ids[::-1]
    filtered = client.get("/api/v1/tasks", headers=headers, params={"q": "%_"}).json()
    assert [task["id"] for task in filtered] == ids[:1]
    filtered = client.get(
        "/api/v1/tasks", headers=headers, params={"q": "api", "status": "completed"}
    ).json()
    assert [task["id"] for task in filtered] == ids[:1]
    assert (
        client.get(
            "/api/v1/tasks", headers=headers, params={"status": "invalid"}
        ).status_code
        == 422
    )


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"titulo": " "},
        {"titulo": "x" * 201},
        {"titulo": "OK", "user_id": 999},
        {"titulo": "OK", "status": "invalid"},
        {"titulo": "OK", "descricao": "x" * 10001},
    ],
)
def test_create_rejects_invalid_fields(client, payload):
    headers = authenticate(client, "invalid@example.com")
    assert (
        client.post("/api/v1/tasks", headers=headers, json=payload).status_code == 422
    )


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"titulo": None},
        {"descricao": None},
        {"status": None},
        {"titulo": " "},
        {"user_id": 999},
    ],
)
def test_patch_rejects_empty_null_or_owner_fields(client, payload):
    headers = authenticate(client, "patch@example.com")
    task = client.post(
        "/api/v1/tasks", headers=headers, json={"titulo": "Original"}
    ).json()
    assert (
        client.patch(
            f"/api/v1/tasks/{task['id']}", headers=headers, json=payload
        ).status_code
        == 422
    )


@pytest.mark.parametrize(
    "method,path,kwargs",
    [
        ("get", "/api/v1/tasks", {}),
        ("get", "/api/v1/tasks/1", {}),
        ("post", "/api/v1/tasks", {"json": {"titulo": "Teste"}}),
        ("patch", "/api/v1/tasks/1", {"json": {"titulo": "Teste"}}),
        ("delete", "/api/v1/tasks/1", {}),
    ],
)
def test_all_operations_require_authentication(client, method, path, kwargs):
    assert getattr(client, method)(path, **kwargs).status_code == 401


@pytest.mark.parametrize("task_id", [0, -1, 2**63])
@pytest.mark.parametrize("method", ["get", "patch", "delete"])
def test_task_ids_are_bounded(client, task_id, method):
    headers = authenticate(client, "ids@example.com")
    kwargs = {"json": {"titulo": "Teste"}} if method == "patch" else {}
    assert (
        getattr(client, method)(
            f"/api/v1/tasks/{task_id}", headers=headers, **kwargs
        ).status_code
        == 422
    )
