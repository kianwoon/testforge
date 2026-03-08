import pytest
import tempfile
import os
from fastapi.testclient import TestClient
from agent.main import app
from agent.models import TestCaseSpec

@pytest.mark.asyncio
async def test_submit_test_case_endpoint():
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ["SHARED_VOLUME_PATH"] = tmpdir

        # Reset the global manifest manager to use new temp directory
        import agent.api
        agent.api._manifest_manager = None

        client = TestClient(app)
        test_case = {
            "name": "Test login",
            "scope": "Auth",
            "steps": ["Step 1", "Step 2"],
            "specs": ["Spec 1"]
        }

        response = client.post("/api/v1/submit", json=test_case)
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data

@pytest.mark.asyncio
async def test_get_status_endpoint():
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ["SHARED_VOLUME_PATH"] = tmpdir

        # Reset the global manifest manager to use new temp directory
        import agent.api
        agent.api._manifest_manager = None

        client = TestClient(app)
        test_case = {"name": "Test", "scope": "Auth", "steps": ["Step 1"], "specs": ["Spec 1"]}

        submit_response = client.post("/api/v1/submit", json=test_case)
        job_id = submit_response.json()["job_id"]

        status_response = client.get(f"/api/v1/status/{job_id}")
        assert status_response.status_code == 200
        data = status_response.json()
        assert data["job_id"] == job_id
