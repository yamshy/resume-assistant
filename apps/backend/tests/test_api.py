import pytest
from httpx import ASGITransport, AsyncClient

from app.api import app, get_temporal_client
from app.state import initialize_state


class DummyHandle:
    def __init__(self, state):
        self.id = state.request_id
        self.run_id = "run-001"
        self._state = state
        self.signals = []

    async def query(self, _method):
        return self._state

    async def signal(self, _method, *args, **kwargs):
        if "args" in kwargs:
            approved, notes = kwargs["args"]
        else:
            approved, notes = args
        self.signals.append((bool(approved), notes))

    async def result(self):
        return self._state


class DummyClient:
    def __init__(self, state):
        self.state = state
        self.handle = DummyHandle(state)
        self.started_with = None

    async def start_workflow(self, *_args, **_kwargs):
        self.started_with = {"args": _args, "kwargs": _kwargs}
        return self.handle

    def get_workflow_handle(self, workflow_id: str):
        if workflow_id != self.state.request_id:
            raise RuntimeError("unknown workflow")
        return self.handle


@pytest.fixture
async def api_client():
    state = initialize_state(task="resume_pipeline", request_id="req-123")
    dummy_client = DummyClient(state)

    async def override_client():
        return dummy_client

    app.dependency_overrides[get_temporal_client] = override_client
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client, dummy_client
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_start_workflow(api_client):
    client, dummy = api_client
    response = await client.post("/workflows/resume", json={"task": "resume_pipeline", "request_id": "req-123"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["workflow_id"] == "req-123"
    assert dummy.started_with is not None


@pytest.mark.asyncio
async def test_health_check(api_client):
    client, _dummy = api_client
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_get_workflow_state(api_client):
    client, _dummy = api_client
    response = await client.get("/workflows/req-123")
    assert response.status_code == 200
    state = response.json()["state"]
    assert state["request_id"] == "req-123"


@pytest.mark.asyncio
async def test_submit_approval(api_client):
    client, dummy = api_client
    response = await client.post("/workflows/req-123/approval", json={"approved": True, "notes": "ok"})
    assert response.status_code == 202
    assert dummy.handle.signals == [(True, "ok")]


@pytest.mark.asyncio
async def test_get_result(api_client):
    client, _dummy = api_client
    response = await client.get("/workflows/req-123/result")
    assert response.status_code == 200
    assert response.json()["state"]["status"] == "pending"
