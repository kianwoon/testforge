# bot/tests/test_agent_client.py
import pytest
from unittest.mock import AsyncMock, Mock, patch
from bot.agent_client import AgentAPIClient
from bot.models import TestCaseSpec


@pytest.mark.asyncio
async def test_submit_test_case_success():
    """Test successful test case submission returns job_id."""
    client = AgentAPIClient(base_url="http://localhost:8000")
    test_case = TestCaseSpec(
        name="Login Test",
        scope="Auth",
        steps=["Step 1", "Step 2"]
    )

    # Create a mock response
    mock_response = Mock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={"job_id": "test-job-id", "status": "queued"})

    # Create mock post method that returns an async context manager
    mock_post_cm = AsyncMock()
    mock_post_cm.__aenter__ = AsyncMock(return_value=mock_response)
    mock_post_cm.__aexit__ = AsyncMock(return_value=None)

    mock_session = AsyncMock()
    mock_session.post = Mock(return_value=mock_post_cm)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)

    # Patch the ClientSession constructor
    with patch('bot.agent_client.aiohttp.ClientSession', return_value=mock_session):
        job_id = await client.submit_test_case(test_case)

    assert job_id == "test-job-id"


@pytest.mark.asyncio
async def test_submit_test_case_failure():
    """Test test case submission handles API errors."""
    client = AgentAPIClient(base_url="http://localhost:8000")
    test_case = TestCaseSpec(
        name="Login Test",
        scope="Auth",
        steps=["Step 1"]
    )

    # Create a mock error response
    mock_response = Mock()
    mock_response.status = 500
    mock_response.text = AsyncMock(return_value="Internal Server Error")

    mock_post_cm = AsyncMock()
    mock_post_cm.__aenter__ = AsyncMock(return_value=mock_response)
    mock_post_cm.__aexit__ = AsyncMock(return_value=None)

    mock_session = AsyncMock()
    mock_session.post = Mock(return_value=mock_post_cm)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)

    with patch('bot.agent_client.aiohttp.ClientSession', return_value=mock_session):
        with pytest.raises(Exception) as exc_info:
            await client.submit_test_case(test_case)

    assert "Agent returned 500" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_job_status_success():
    """Test successful job status retrieval."""
    client = AgentAPIClient(base_url="http://localhost:8000")

    mock_response = Mock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={
        "job_id": "test-job-id",
        "status": "completed",
        "created_at": "2026-03-08T15:00:00Z"
    })

    mock_get_cm = AsyncMock()
    mock_get_cm.__aenter__ = AsyncMock(return_value=mock_response)
    mock_get_cm.__aexit__ = AsyncMock(return_value=None)

    mock_session = AsyncMock()
    mock_session.get = Mock(return_value=mock_get_cm)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)

    with patch('bot.agent_client.aiohttp.ClientSession', return_value=mock_session):
        status = await client.get_status("test-job-id")

    assert status["job_id"] == "test-job-id"
    assert status["status"] == "completed"


@pytest.mark.asyncio
async def test_get_job_status_not_found():
    """Test job status retrieval handles 404 errors."""
    client = AgentAPIClient(base_url="http://localhost:8000")

    mock_response = Mock()
    mock_response.status = 404

    mock_get_cm = AsyncMock()
    mock_get_cm.__aenter__ = AsyncMock(return_value=mock_response)
    mock_get_cm.__aexit__ = AsyncMock(return_value=None)

    mock_session = AsyncMock()
    mock_session.get = Mock(return_value=mock_get_cm)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)

    with patch('bot.agent_client.aiohttp.ClientSession', return_value=mock_session):
        with pytest.raises(Exception) as exc_info:
            await client.get_status("non-existent-job-id")

    assert "not found" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_get_generated_script_completed():
    """Test script retrieval for completed job."""
    client = AgentAPIClient(base_url="http://localhost:8000")

    mock_response = Mock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={
        "job_id": "test-job-id",
        "status": "completed",
        "created_at": "2026-03-08T15:00:00Z"
    })

    mock_get_cm = AsyncMock()
    mock_get_cm.__aenter__ = AsyncMock(return_value=mock_response)
    mock_get_cm.__aexit__ = AsyncMock(return_value=None)

    mock_session = AsyncMock()
    mock_session.get = Mock(return_value=mock_get_cm)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)

    with patch('bot.agent_client.aiohttp.ClientSession', return_value=mock_session):
        script = await client.get_generated_script("test-job-id")

    assert script is not None
    assert "test-job-id" in script


@pytest.mark.asyncio
async def test_get_generated_script_pending():
    """Test script retrieval returns None for non-completed job."""
    client = AgentAPIClient(base_url="http://localhost:8000")

    mock_response = Mock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={
        "job_id": "test-job-id",
        "status": "processing",
        "created_at": "2026-03-08T15:00:00Z"
    })

    mock_get_cm = AsyncMock()
    mock_get_cm.__aenter__ = AsyncMock(return_value=mock_response)
    mock_get_cm.__aexit__ = AsyncMock(return_value=None)

    mock_session = AsyncMock()
    mock_session.get = Mock(return_value=mock_get_cm)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)

    with patch('bot.agent_client.aiohttp.ClientSession', return_value=mock_session):
        script = await client.get_generated_script("test-job-id")

    assert script is None
