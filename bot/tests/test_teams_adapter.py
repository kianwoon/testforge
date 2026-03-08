# bot/tests/test_teams_adapter.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from bot.teams_adapter import TeamsMessageAdapter
from bot.models import TestCaseSpec

@pytest.mark.asyncio
async def test_extract_test_case_from_message():
    """Test extracting test case from Teams message."""
    adapter = TeamsMessageAdapter()

    message = """
Test: Login validation
Scope: Authentication Module
Steps:
1. Navigate to /login
2. Enter invalid credentials
3. Verify error message
"""

    test_case = await adapter.parse_message(message)

    assert test_case is not None
    assert test_case.name == "Login validation"
    assert test_case.scope == "Authentication Module"
    assert len(test_case.steps) == 3
    assert test_case.steps[0] == "Navigate to /login"

@pytest.mark.asyncio
async def test_format_status_message():
    """Test formatting job status for Teams."""
    adapter = TeamsMessageAdapter()

    status = {
        "job_id": "job-123",
        "status": "completed",
        "test_case": {
            "name": "Login test"
        },
        "created_at": "2026-03-08T10:00:00Z"
    }

    formatted = await adapter.format_status(status)

    assert "job-123" in formatted
    assert "completed" in formatted
    assert "Login test" in formatted

@pytest.mark.asyncio
async def test_format_error_message():
    """Test formatting error message for Teams."""
    adapter = TeamsMessageAdapter()

    error = "Validation failed: Missing required field 'scope'"

    formatted = await adapter.format_error(error)

    assert "❌" in formatted or "Error" in formatted
    assert "Missing required field" in formatted

@pytest.mark.asyncio
async def test_parse_empty_message():
    """Test parsing empty message returns None."""
    adapter = TeamsMessageAdapter()
    result = await adapter.parse_message("")
    assert result is None

@pytest.mark.asyncio
async def test_parse_whitespace_message():
    """Test parsing whitespace-only message returns None."""
    adapter = TeamsMessageAdapter()
    result = await adapter.parse_message("   \n\t  ")
    assert result is None

@pytest.mark.asyncio
async def test_format_status_with_missing_fields():
    """Test formatting status with incomplete data."""
    adapter = TeamsMessageAdapter()

    # Missing test_case
    status = {"job_id": "job-123", "status": "pending"}
    formatted = await adapter.format_status(status)
    assert "job-123" in formatted
    assert "Unknown Test" in formatted

@pytest.mark.asyncio
async def test_format_error_with_long_message():
    """Test formatting long error message."""
    adapter = TeamsMessageAdapter()
    long_error = "Error: " + "x" * 500
    formatted = await adapter.format_error(long_error)
    assert "Error:" in formatted
