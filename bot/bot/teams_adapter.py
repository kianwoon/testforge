# bot/bot/teams_adapter.py
import logging
from bot.test_case_parser import TestCaseParser
from bot.models import TestCaseSpec
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class TeamsMessageAdapter:
    """Adapter for formatting messages between Teams and internal formats."""

    def __init__(self):
        self.parser = TestCaseParser()

    async def parse_message(self, message: str) -> Optional[TestCaseSpec]:
        """
        Parse Teams message text into TestCaseSpec.

        Args:
            message: Raw message text from Teams

        Returns:
            TestCaseSpec if valid, None otherwise
        """
        try:
            # Validate message is not empty or whitespace
            if not message or not message.strip():
                logger.warning("Empty or whitespace-only message received")
                return None

            return await self.parser.parse(message)
        except Exception as e:
            logger.warning(f"Failed to parse Teams message: {e}")
            return None

    async def format_status(self, status: Dict[str, Any]) -> str:
        """
        Format job status for Teams message.

        Args:
            status: Job status dictionary from Agent API

        Returns:
            Formatted message string for Teams
        """
        job_id = status.get("job_id", "unknown")
        job_status = status.get("status", "unknown")
        test_name = status.get("test_case", {}).get("name", "Unknown Test")

        status_emoji = {
            "pending": "⏳",
            "processing": "⚙️",
            "completed": "✅",
            "failed": "❌"
        }.get(job_status, "❓")

        return f"""
{status_emoji} **Job Status**

**Test:** {test_name}
**Job ID:** {job_id}
**Status:** {job_status}
"""

    async def format_error(self, error: str) -> str:
        """
        Format error message for Teams.

        Args:
            error: Error message

        Returns:
            Formatted error string for Teams
        """
        return f"""
❌ **Error**

{error}

Please check your test case format and try again.
"""
