# bot/tests/test_teams_bot.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from bot.teams_bot import NanoClawTeamsBot
from bot.models import TestCaseSpec, ConversationState
from botbuilder.schema import Activity, ActivityTypes


@pytest.mark.asyncio
async def test_bot_handles_test_case_submission():
    """Test bot receives and processes test case message."""
    conversation_manager = AsyncMock()
    agent_client = AsyncMock()
    agent_client.submit_test_case.return_value = "job-123"

    bot = NanoClawTeamsBot(conversation_manager, agent_client)

    message = Activity(
        type=ActivityTypes.message,
        text="Test: Login test\nScope: Auth\nSteps:\n1. Go to login",
        from_property=MagicMock(id="user-123")
    )

    response = await bot.on_message_activity(message)

    assert response is not None
    assert "job-123" in response or "submitted" in response.lower()
    conversation_manager.update_state.assert_called_once()


@pytest.mark.asyncio
async def test_bot_handles_status_query():
    """Test bot responds to status query."""
    conversation_manager = AsyncMock()
    agent_client = AsyncMock()
    agent_client.get_status.return_value = {
        "job_id": "job-123",
        "status": "completed",
        "test_case": {"name": "Login test"}
    }

    bot = NanoClawTeamsBot(conversation_manager, agent_client)

    message = Activity(
        type=ActivityTypes.message,
        text="status job-123",
        from_property=MagicMock(id="user-123")
    )

    response = await bot.on_message_activity(message)

    assert response is not None
    assert "completed" in response.lower()
    agent_client.get_status.assert_called_once_with("job-123")


@pytest.mark.asyncio
async def test_bot_handles_help_command():
    """Test bot responds to help command."""
    conversation_manager = AsyncMock()
    agent_client = AsyncMock()

    bot = NanoClawTeamsBot(conversation_manager, agent_client)

    message = Activity(
        type=ActivityTypes.message,
        text="help",
        from_property=MagicMock(id="user-123")
    )

    response = await bot.on_message_activity(message)

    assert response is not None
    assert "help" in response.lower() or "usage" in response.lower() or "test" in response.lower()


@pytest.mark.asyncio
async def test_bot_handles_status_not_found():
    """Test bot handles status query for non-existent job."""
    conversation_manager = AsyncMock()
    agent_client = AsyncMock()
    agent_client.get_status.side_effect = Exception("Job not found")

    bot = NanoClawTeamsBot(conversation_manager, agent_client)

    message = Activity(
        type=ActivityTypes.message,
        text="status invalid-job-id",
        from_property=MagicMock(id="user-123")
    )

    response = await bot.on_message_activity(message)

    assert response is not None
    assert "error" in response.lower()


@pytest.mark.asyncio
async def test_bot_handles_minimal_test_case():
    """Test bot handles minimal/loose test case format (parser is lenient)."""
    conversation_manager = AsyncMock()
    agent_client = AsyncMock()
    agent_client.submit_test_case.return_value = "job-456"

    bot = NanoClawTeamsBot(conversation_manager, agent_client)

    message = Activity(
        type=ActivityTypes.message,
        text="just some random text",
        from_property=MagicMock(id="user-123")
    )

    response = await bot.on_message_activity(message)

    # Parser is lenient and creates a test case with default values
    assert response is not None
    assert "job-456" in response or "submitted" in response.lower()
    agent_client.submit_test_case.assert_called_once()


@pytest.mark.asyncio
async def test_bot_handles_api_error():
    """Test bot handles Agent API error during submission."""
    conversation_manager = AsyncMock()
    agent_client = AsyncMock()
    agent_client.submit_test_case.side_effect = Exception("API Error")

    bot = NanoClawTeamsBot(conversation_manager, agent_client)

    message = Activity(
        type=ActivityTypes.message,
        text="Test: Login test\nScope: Auth\nSteps:\n1. Go to login",
        from_property=MagicMock(id="user-123")
    )

    response = await bot.on_message_activity(message)

    assert response is not None
    assert "error" in response.lower()
    # Conversation state should NOT be updated on error
    conversation_manager.update_state.assert_not_called()
