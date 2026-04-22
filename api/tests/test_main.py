from unittest.mock import MagicMock, patch

# Patch redis.Redis before main is imported so the module-level
# `r = redis.Redis(...)` call receives our mock instance.
_mock_r = MagicMock()

with patch("redis.Redis", return_value=_mock_r):
    from main import app

from fastapi.testclient import TestClient

client = TestClient(app)


def setup_function():
    _mock_r.reset_mock()


def test_health_returns_healthy():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_create_job_returns_job_id():
    response = client.post("/jobs")
    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data
    assert len(data["job_id"]) == 36  # UUID4


def test_create_job_pushes_to_redis_queue():
    response = client.post("/jobs")
    job_id = response.json()["job_id"]
    _mock_r.lpush.assert_called_once_with("job", job_id)
    _mock_r.hset.assert_called_once_with(f"job:{job_id}", "status", "queued")


def test_get_job_existing_returns_status():
    _mock_r.hget.return_value = b"queued"
    response = client.get("/jobs/test-job-123")
    assert response.status_code == 200
    data = response.json()
    assert data["job_id"] == "test-job-123"
    assert data["status"] == "queued"


def test_get_job_not_found_returns_error():
    _mock_r.hget.return_value = None
    response = client.get("/jobs/nonexistent-id")
    assert response.status_code == 200
    assert response.json() == {"error": "not found"}
