# bot/tests/test_conversation.py
import pytest
from bot.conversation_manager import ConversationManager
from bot.models import ConversationState, TestCaseSpec

@pytest.mark.asyncio
async def test_create_and_get_conversation():
    manager = ConversationManager()
    await manager.update_state(
        user_id="wa_123",
        state=ConversationState.IDLE
    )
    state = await manager.get_state("wa_123")
    assert state.user_id == "wa_123"
    assert state.state == ConversationState.IDLE

@pytest.mark.asyncio
async def test_update_conversation_with_test_case():
    manager = ConversationManager()
    test_case = TestCaseSpec(
        name="Test",
        scope="Auth",
        steps=["Step 1"]
    )
    await manager.update_state(
        user_id="wa_456",
        state=ConversationState.AWAITING_TEST_CASE,
        test_case_draft=test_case
    )
    state = await manager.get_state("wa_456")
    assert state.state == ConversationState.AWAITING_TEST_CASE
    assert state.test_case_draft.name == "Test"
