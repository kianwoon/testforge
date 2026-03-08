# bot/bot/conversation_manager.py
from datetime import datetime, timedelta
from typing import Dict, Optional
from .models import ConversationState, TestCaseSpec, ConversationData

class ConversationManager:
    def __init__(self, ttl_minutes: int = 30):
        # In production, use Redis or database
        self._conversations: Dict[str, ConversationData] = {}
        self.ttl = timedelta(minutes=ttl_minutes)

    async def get_state(self, user_id: str) -> Optional[ConversationData]:
        state = self._conversations.get(user_id)
        # Check if expired
        if state and datetime.utcnow() - state.created_at > self.ttl:
            del self._conversations[user_id]
            return None
        return state

    async def update_state(
        self,
        user_id: str,
        state: ConversationState,
        test_case_draft: Optional[TestCaseSpec] = None,
        current_job_id: Optional[str] = None
    ) -> None:
        existing = await self.get_state(user_id)

        if existing:
            existing.state = state
            existing.test_case_draft = test_case_draft or existing.test_case_draft
            existing.current_job_id = current_job_id or existing.current_job_id
        else:
            self._conversations[user_id] = ConversationData(
                user_id=user_id,
                state=state,
                test_case_draft=test_case_draft,
                current_job_id=current_job_id
            )

    async def clear_state(self, user_id: str) -> None:
        if user_id in self._conversations:
            del self._conversations[user_id]
