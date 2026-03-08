# bot/bot/teams_bot.py
import logging
from botbuilder.core import ActivityHandler
from botbuilder.schema import Activity
from .conversation_manager import ConversationManager
from .agent_client import AgentAPIClient
from .teams_adapter import TeamsMessageAdapter
from .models import ConversationState

logger = logging.getLogger(__name__)


class NanoClawTeamsBot(ActivityHandler):
    """Teams bot handler for NanoClaw test automation."""

    def __init__(
        self,
        conversation_manager: ConversationManager,
        agent_client: AgentAPIClient
    ):
        """
        Initialize the Teams bot.

        Args:
            conversation_manager: Manager for conversation state
            agent_client: Client for Agent API communication
        """
        self.conversation_manager = conversation_manager
        self.agent_client = agent_client
        self.message_adapter = TeamsMessageAdapter()

    async def on_message_activity(self, activity: Activity) -> str:
        """
        Handle incoming message activities.

        Args:
            activity: The incoming activity from Teams

        Returns:
            Response text to send back to user
        """
        try:
            user_id = activity.from_property.id
            message_text = activity.text.strip().lower()

            logger.info(f"Received message from {user_id}: {message_text}")

            # Route to appropriate handler based on message content
            if message_text == "help":
                return await self._handle_help()
            elif message_text.startswith("status "):
                job_id = message_text.split(" ", 1)[1].strip()
                return await self._handle_status(job_id)
            else:
                # Try to parse as test case
                return await self._handle_test_case(activity.text, user_id)

        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            return await self.message_adapter.format_error(str(e))

    async def _handle_help(self) -> str:
        """Handle help command."""
        return """
**NanoClaw Bot Help**

I help you generate Playwright test scripts from natural language test cases.

**Commands:**
- `help` - Show this help message
- `status <job-id>` - Check status of a submitted job
- `<test case>` - Submit a new test case

**Test Case Format:**
```
Test: <test name>
Scope: <module/feature>
Priority: P0|P1|P2

Specs:
- <requirement 1>
- <requirement 2>

Steps:
1. <step 1>
2. <step 2>
```

**Example:**
```
Test: Login test
Scope: Auth
Priority: P1

Steps:
1. Navigate to login page
2. Enter valid credentials
3. Click login button
4. Verify user is redirected to dashboard
```
"""

    async def _handle_status(self, job_id: str) -> str:
        """
        Handle status query for a job.

        Args:
            job_id: The job ID to query

        Returns:
            Formatted status message
        """
        try:
            status = await self.agent_client.get_status(job_id)
            return await self.message_adapter.format_status(status)
        except Exception as e:
            logger.error(f"Error fetching status for job {job_id}: {e}")
            return await self.message_adapter.format_error(
                f"Failed to fetch status for job {job_id}: {str(e)}"
            )

    async def _handle_test_case(self, message: str, user_id: str) -> str:
        """
        Handle test case submission.

        Args:
            message: The raw message text
            user_id: The user ID

        Returns:
            Response with job ID or error message
        """
        # Parse the test case
        test_case = await self.message_adapter.parse_message(message)

        if not test_case:
            return await self.message_adapter.format_error(
                "Failed to parse test case. Please check the format and try again."
            )

        # Submit to Agent API
        try:
            job_id = await self.agent_client.submit_test_case(test_case)
            logger.info(f"Submitted test case, job_id: {job_id}")

            # Update conversation state
            await self.conversation_manager.update_state(
                user_id=user_id,
                state=ConversationState.PROCESSING,
                test_case_draft=test_case,
                current_job_id=job_id
            )

            return f"""
✅ **Test Case Submitted**

**Test:** {test_case.name}
**Job ID:** {job_id}

Use `status {job_id}` to check progress.
"""

        except Exception as e:
            logger.error(f"Error submitting test case: {e}")
            return await self.message_adapter.format_error(
                f"Failed to submit test case: {str(e)}"
            )
