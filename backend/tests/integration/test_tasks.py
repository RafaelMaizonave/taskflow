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
    assert task["status"] == "backlog"
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
    updated = client.patch(path, headers=owner, json={"status": "done"})
    assert updated.status_code == 200
    assert updated.json()["descricao"] == "Detalhes"
    assert updated.json()["status"] == "done"
    assert client.delete(path, headers=owner).status_code == 204
    assert client.get(path, headers=owner).status_code == 404


def test_filters_are_literal_and_order_is_deterministic(client):
    headers = authenticate(client, "filter@example.com")
    tasks = [
        {"titulo": "API 100%_pronta", "status": "done"},
        {"titulo": "API 100xxpronta"},
        {"titulo": "Outra"},
    ]
    ids = [
        client.post("/api/v1/tasks", headers=headers, json=task).json()["id"]
        for task in tasks
    ]
    assert [
        task["id"] for task in client.get("/api/v1/tasks", headers=headers).json()
    ] == [ids[1], ids[0], ids[2]]
    filtered = client.get("/api/v1/tasks", headers=headers, params={"q": "%_"}).json()
    assert [task["id"] for task in filtered] == ids[:1]
    filtered = client.get(
        "/api/v1/tasks", headers=headers, params={"q": "api", "status": "done"}
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


def test_task_metadata_completion_and_owner_protection(client):
    owner = authenticate(client, "metadata@example.com")
    other = authenticate(client, "outsider@example.com")
    response = client.post(
        "/api/v1/tasks",
        headers=owner,
        json={
            "titulo": "Planejar",
            "priority": "high",
            "due_date": "2026-11-01",
            "tags": [" Produto ", "Produto"],
            "position": 4,
        },
    )
    assert response.status_code == 201
    task = response.json()
    assert task["tags"] == ["Produto"]
    assert task["priority"] == "high"
    assert task["due_date"] == "2026-11-01"
    path = f"/api/v1/tasks/{task['id']}"
    assert client.patch(path, headers=other, json={"position": 0}).status_code == 404
    done = client.patch(
        path, headers=owner, json={"status": "done", "position": 0}
    ).json()
    assert done["completed_at"] is not None
    assert done["updated_at"] >= task["updated_at"]
    assert done["position"] == 0
    reopened = client.patch(
        path, headers=owner, json={"status": "backlog", "due_date": None}
    ).json()
    assert reopened["completed_at"] is None
    assert reopened["due_date"] is None
    assert client.get(path, headers=owner).json() == reopened


@pytest.mark.parametrize(
    "changes",
    [
        {"priority": "urgent"},
        {"tags": [""]},
        {"tags": ["a"] * 11},
        {"tags": ["x" * 41]},
        {"due_date": "tomorrow"},
        {"position": -1},
        {"position": True},
        {"position": None},
    ],
)
def test_task_metadata_validation(client, changes):
    headers = authenticate(client, "metadata-validation@example.com")
    task = client.post(
        "/api/v1/tasks", headers=headers, json={"titulo": "Teste"}
    ).json()
    assert (
        client.patch(
            f"/api/v1/tasks/{task['id']}", headers=headers, json=changes
        ).status_code
        == 422
    )
