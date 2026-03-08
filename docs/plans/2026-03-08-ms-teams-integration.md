# MS Teams Integration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add Microsoft Teams bot integration as an alternative communication channel to WhatsApp, allowing users to submit test cases and receive notifications via Teams.

**Architecture:** Multi-channel bot architecture with shared core components. Teams bot will run in separate container alongside existing WhatsApp bot, sharing ConversationManager and AgentAPIClient through dependency injection. Teams-specific adapter handles webhook events and message formatting.

**Tech Stack:** Python 3.11+, Microsoft Bot Framework SDK (botbuilder-core), aiohttp, FastAPI, Docker

---

## Phase 1: Teams Bot Foundation

### Task 1: Add Bot Framework Dependencies

**Files:**
- Modify: `bot/requirements.txt`

**Step 1: Add Microsoft Bot Framework packages**

```bash
cat >> bot/requirements.txt << 'EOF'

# Microsoft Teams Bot Framework
botbuilder-core==4.14.3
botbuilder-schema==4.14.3
botbuilder-integration-aiohttp==4.14.3
EOF
```

**Step 2: Install dependencies**

Run: `pip install -r bot/requirements.txt`
Expected: Successfully installed botbuilder-* packages

**Step 3: Commit**

```bash
git add bot/requirements.txt
git commit -m "chore: add Microsoft Bot Framework dependencies"
```

---

### Task 2: Create Teams Configuration Model

**Files:**
- Create: `bot/bot/teams_config.py`
- Test: `bot/tests/test_teams_config.py`

**Step 1: Write the failing test**

```python
# bot/tests/test_teams_config.py
import pytest
from bot.teams_config import TeamsConfig

def test_teams_config_defaults():
    """Test Teams configuration with default values."""
    config = TeamsConfig(
        app_id="test-app-id",
        app_password="test-password"
    )

    assert config.app_id == "test-app-id"
    assert config.app_password == "test-password"
    assert config.port == 3978  # Default Teams bot port

def test_teams_config_custom_port():
    """Test Teams configuration with custom port."""
    config = TeamsConfig(
        app_id="test-app-id",
        app_password="test-password",
        port=5000
    )

    assert config.port == 5000

def test_teams_config_validation():
    """Test that missing credentials raise error."""
    with pytest.raises(ValueError):
        TeamsConfig(app_id="", app_password="test")

    with pytest.raises(ValueError):
        TeamsConfig(app_id="test", app_password="")
```

**Step 2: Run test to verify it fails**

Run: `pytest bot/tests/test_teams_config.py -v`
Expected: FAIL - ModuleNotFoundError

**Step 3: Write minimal implementation**

```python
# bot/bot/teams_config.py
from pydantic import BaseModel, Field, field_validator


class TeamsConfig(BaseModel):
    """Configuration for Microsoft Teams bot."""

    app_id: str = Field(..., description="Microsoft Teams App ID")
    app_password: str = Field(..., description="Microsoft Teams App Password")
    port: int = Field(default=3978, description="Port for Teams bot server")

    @field_validator('app_id')
    @classmethod
    def validate_app_id(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('App ID cannot be empty')
        return v

    @field_validator('app_password')
    @classmethod
    def validate_app_password(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('App password cannot be empty')
        return v
```

**Step 4: Run test to verify it passes**

Run: `pytest bot/tests/test_teams_config.py -v`
Expected: PASS - 3 tests

**Step 5: Commit**

```bash
git add bot/bot/teams_config.py bot/tests/test_teams_config.py
git commit -m "feat: add Teams configuration model"
```

---

### Task 3: Create Teams Message Adapter

**Files:**
- Create: `bot/bot/teams_adapter.py`
- Test: `bot/tests/test_teams_adapter.py`

**Step 1: Write the failing test**

```python
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
```

**Step 2: Run test to verify it fails**

Run: `pytest bot/tests/test_teams_adapter.py -v`
Expected: FAIL - ModuleNotFoundError

**Step 3: Write minimal implementation**

```python
# bot/bot/teams_adapter.py
from bot.test_case_parser import TestCaseParser
from typing import Optional, Dict, Any


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
            return await self.parser.parse(message)
        except Exception:
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
```

**Step 4: Run test to verify it passes**

Run: `pytest bot/tests/test_teams_adapter.py -v`
Expected: PASS - 3 tests

**Step 5: Commit**

```bash
git add bot/bot/teams_adapter.py bot/tests/test_teams_adapter.py
git commit -m "feat: add Teams message adapter"
```

---

### Task 4: Create Teams Bot Handler

**Files:**
- Create: `bot/bot/teams_bot.py`
- Test: `bot/tests/test_teams_bot.py`

**Step 1: Write the failing test**

```python
# bot/tests/test_teams_bot.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from bot.teams_bot import NanoClawTeamsBot
from bot.models import TestCaseSpec, ConversationState
from botbuilder.schema import Activity, ActivityTypes

@pytest.mark.asyncio
async def test_bot_handles_test_case_submission():
    """Test bot receives and processes test case message."""
    # Mock dependencies
    conversation_manager = AsyncMock()
    agent_client = AsyncMock()
    agent_client.submit_test_case.return_value = "job-123"

    bot = NanoClawTeamsBot(conversation_manager, agent_client)

    # Create test message
    message = Activity(
        type=ActivityTypes.message,
        text="""
Test: Login test
Scope: Auth
Steps:
1. Go to login
""",
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
        "status": "completed"
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
```

**Step 2: Run test to verify it fails**

Run: `pytest bot/tests/test_teams_bot.py -v`
Expected: FAIL - ModuleNotFoundError

**Step 3: Write minimal implementation**

```python
# bot/bot/teams_bot.py
from botbuilder.core import ActivityHandler, TurnContext
from botbuilder.schema import Activity, ActivityTypes
from bot.conversation_manager import ConversationManager
from bot.agent_client import AgentAPIClient
from bot.teams_adapter import TeamsMessageAdapter
from bot.models import ConversationState
from typing import Optional


class NanoClawTeamsBot(ActivityHandler):
    """
    Microsoft Teams bot handler for NanoClaw.
    Handles incoming messages and routes to appropriate handlers.
    """

    def __init__(
        self,
        conversation_manager: ConversationManager,
        agent_client: AgentAPIClient
    ):
        """
        Initialize Teams bot.

        Args:
            conversation_manager: Shared conversation state manager
            agent_client: Client for Agent API communication
        """
        self.conversation_manager = conversation_manager
        self.agent_client = agent_client
        self.adapter = TeamsMessageAdapter()

    async def on_message_activity(self, turn_context: TurnContext) -> str:
        """
        Handle incoming message from Teams.

        Args:
            turn_context: Bot framework turn context

        Returns:
            Response message to send back to user
        """
        user_id = turn_context.activity.from_property.id
        message_text = turn_context.activity.text.strip()

        # Check for status query
        if message_text.lower().startswith("status "):
            return await self._handle_status_query(user_id, message_text)

        # Check for help command
        if message_text.lower() in ["help", "?"]:
            return await self._get_help_message()

        # Try to parse as test case
        test_case = await self.adapter.parse_message(message_text)

        if test_case:
            return await self._handle_test_case_submission(user_id, test_case)
        else:
            return await self.adapter.format_error(
                "Could not parse test case. Please use the correct format.\\n"
                "Type 'help' for usage instructions."
            )

    async def _handle_test_case_submission(
        self,
        user_id: str,
        test_case
    ) -> str:
        """Submit test case to Agent API."""
        try:
            job_id = await self.agent_client.submit_test_case(test_case)

            # Update conversation state
            await self.conversation_manager.update_state(
                user_id=user_id,
                state=ConversationState.PROCESSING,
                current_job_id=job_id
            )

            return f"✅ Test case submitted successfully!\\n\\n**Job ID:** {job_id}\\n\\nUse `status {job_id}` to check progress."

        except Exception as e:
            return await self.adapter.format_error(f"Failed to submit test case: {str(e)}")

    async def _handle_status_query(self, user_id: str, message: str) -> str:
        """Handle status query command."""
        # Extract job ID from message
        parts = message.split(maxsplit=1)
        if len(parts) < 2:
            return "Please provide a job ID: `status <job-id>`"

        job_id = parts[1].strip()

        try:
            status = await self.agent_client.get_status(job_id)
            return await self.adapter.format_status(status)
        except Exception as e:
            return await self.adapter.format_error(f"Failed to get status: {str(e)}")

    async def _get_help_message(self) -> str:
        """Get help message for Teams users."""
        return """
🤖 **NanoClaw Bot Help**

**Submit a test case:**
```
Test: [Test name]
Scope: [Module/feature]
Steps:
1. [First step]
2. [Second step]
...
```

**Check status:**
```
status <job-id>
```

**Example:**
```
Test: Login validation
Scope: Authentication Module
Steps:
1. Navigate to /login
2. Enter invalid credentials
3. Verify error message
```
"""
```

**Step 4: Run test to verify it passes**

Run: `pytest bot/tests/test_teams_bot.py -v`
Expected: PASS - 2 tests

**Step 5: Commit**

```bash
git add bot/bot/teams_bot.py bot/tests/test_teams_bot.py
git commit -m "feat: add Teams bot handler"
```

---

### Task 5: Create Teams Webhook Server

**Files:**
- Create: `bot/bot/teams_server.py`
- Test: `bot/tests/test_teams_server.py`

**Step 1: Write the failing test**

```python
# bot/tests/test_teams_server.py
import pytest
from aiohttp import web
from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop
from unittest.mock import AsyncMock, MagicMock
from bot.teams_server import create_teams_server
from bot.conversation_manager import ConversationManager
from bot.agent_client import AgentAPIClient

class TestTeamsServer(AioHTTPTestCase):
    async def get_application(self):
        """Create test application."""
        conversation_manager = AsyncMock(spec=ConversationManager)
        agent_client = AsyncMock(spec=AgentAPIClient)

        app = await create_teams_server(
            app_id="test-id",
            app_password="test-password",
            conversation_manager=conversation_manager,
            agent_client=agent_client,
            port=3978
        )
        return app

    @unittest_run_loop
    async def test_health_endpoint(self):
        """Test health check endpoint."""
        resp = await self.client.get("/health")
        assert resp.status == 200
        data = await resp.json()
        assert data["status"] == "healthy"
        assert "teams" in data["service"]

    @unittest_run_loop
    async def test_webhook_endpoint_exists(self):
        """Test webhook endpoint exists."""
        resp = await self.client.post("/api/messages", data="{}")
        # Should get 401 or 403 without valid auth, not 404
        assert resp.status != 404
```

**Step 2: Run test to verify it fails**

Run: `pytest bot/tests/test_teams_server.py -v`
Expected: FAIL - ModuleNotFoundError

**Step 3: Write minimal implementation**

```python
# bot/bot/teams_server.py
from aiohttp import web
from botbuilder.core import BotFrameworkAdapter, BotFrameworkAdapterSettings
from botbuilder.schema import Activity
from bot.conversation_manager import ConversationManager
from bot.agent_client import AgentAPIClient
from bot.teams_bot import NanoClawTeamsBot
import json
import logging

logger = logging.getLogger(__name__)


async def create_teams_server(
    app_id: str,
    app_password: str,
    conversation_manager: ConversationManager,
    agent_client: AgentAPIClient,
    port: int = 3978
) -> web.Application:
    """
    Create and configure Teams bot web server.

    Args:
        app_id: Microsoft Teams App ID
        app_password: Microsoft Teams App Password
        conversation_manager: Shared conversation manager
        agent_client: Agent API client
        port: Server port

    Returns:
        Configured aiohttp Application
    """
    # Create bot adapter
    settings = BotFrameworkAdapterSettings(app_id, app_password)
    adapter = BotFrameworkAdapter(settings)

    # Create bot handler
    bot = NanoClawTeamsBot(conversation_manager, agent_client)

    # Create web application
    app = web.Application()

    # Store bot and adapter in app context
    app["bot"] = bot
    app["adapter"] = adapter

    # Define routes
    async def health_check(request: web.Request) -> web.Response:
        """Health check endpoint."""
        return web.json_response({
            "status": "healthy",
            "service": "teams-bot",
            "port": port
        })

    async def handle_messages(request: web.Request) -> web.Response:
        """Handle incoming Teams messages."""
        try:
            # Parse request body
            body = await request.json()

            # Deserialize to Activity
            activity = Activity().deserialize(body)

            # Get auth header
            auth_header = request.headers.get("Authorization", "")

            # Process activity
            response = await adapter.process_activity(
                auth_header,
                activity,
                bot.on_message_activity
            )

            if response:
                return web.json_response({
                    "type": "message",
                    "text": response
                })
            else:
                return web.Response(status=201)

        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            return web.json_response(
                {"error": "Internal server error"},
                status=500
            )

    # Register routes
    app.router.add_get("/health", health_check)
    app.router.add_post("/api/messages", handle_messages)

    return app


async def run_server(app: web.Application, port: int):
    """Run the web server."""
    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

    logger.info(f"Teams bot server running on port {port}")

    # Keep server running
    while True:
        await asyncio.sleep(3600)
```

**Step 4: Run test to verify it passes**

Run: `pytest bot/tests/test_teams_server.py -v`
Expected: PASS - 2 tests

**Step 5: Commit**

```bash
git add bot/bot/teams_server.py bot/tests/test_teams_server.py
git commit -m "feat: add Teams webhook server"
```

---

## Phase 2: Docker Integration

### Task 6: Create Teams Bot Dockerfile

**Files:**
- Create: `docker/Dockerfile.teams-bot`

**Step 1: Create Dockerfile**

```dockerfile
# docker/Dockerfile.teams-bot
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY bot/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy bot code
COPY bot/ ./bot/
COPY shared/ ./shared/

# Expose port
EXPOSE 3978

# Run Teams bot server
CMD ["python", "-m", "bot.teams_main"]
```

**Step 2: Commit**

```bash
git add docker/Dockerfile.teams-bot
git commit -m "feat: add Teams bot Dockerfile"
```

---

### Task 7: Create Teams Bot Main Entry Point

**Files:**
- Create: `bot/bot/teams_main.py`

**Step 1: Create main entry point**

```python
# bot/bot/teams_main.py
import asyncio
import logging
import os
from bot.teams_server import create_teams_server, run_server
from bot.conversation_manager import ConversationManager
from bot.agent_client import AgentAPIClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Main entry point for Teams bot."""
    # Load configuration from environment
    teams_app_id = os.getenv("TEAMS_APP_ID")
    teams_app_password = os.getenv("TEAMS_APP_PASSWORD")
    teams_port = int(os.getenv("TEAMS_PORT", "3978"))

    # Agent API configuration
    agent_url = os.getenv("AGENT_URL", "http://agent:8000")

    if not teams_app_id or not teams_app_password:
        logger.error("TEAMS_APP_ID and TEAMS_APP_PASSWORD must be set")
        return

    # Initialize shared components
    conversation_manager = ConversationManager()
    agent_client = AgentAPIClient(base_url=agent_url)

    logger.info("Starting Teams bot server...")

    # Create and run server
    app = await create_teams_server(
        app_id=teams_app_id,
        app_password=teams_app_password,
        conversation_manager=conversation_manager,
        agent_client=agent_client,
        port=teams_port
    )

    await run_server(app, teams_port)


if __name__ == "__main__":
    asyncio.run(main())
```

**Step 2: Commit**

```bash
git add bot/bot/teams_main.py
git commit -m "feat: add Teams bot main entry point"
```

---

### Task 8: Update Docker Compose for Teams Bot

**Files:**
- Modify: `docker/docker-compose.yml`

**Step 1: Add Teams bot service**

Add to `docker/docker-compose.yml` after the `bot` service:

```yaml
  teams-bot:
    build:
      context: ..
      dockerfile: docker/Dockerfile.teams-bot
    container_name: nanoclaw-teams-bot
    depends_on:
      - agent
    ports:
      - "3978:3978"
    env_file:
      - ../.env
    environment:
      - PYTHONUNBUFFERED=1
      - AGENT_URL=http://agent:8000
    restart: unless-stopped
```

**Step 2: Commit**

```bash
git add docker/docker-compose.yml
git commit -m "feat: add Teams bot to Docker Compose"
```

---

### Task 9: Update Environment Configuration

**Files:**
- Modify: `.env.example`

**Step 1: Add Teams configuration to .env.example**

Add to `.env.example`:

```bash

# Microsoft Teams Bot Configuration
TEAMS_APP_ID=your_teams_app_id_here
TEAMS_APP_PASSWORD=your_teams_app_password_here
TEAMS_PORT=3978
```

**Step 2: Commit**

```bash
git add .env.example
git commit -m "docs: add Teams bot configuration to .env.example"
```

---

## Phase 3: Documentation

### Task 10: Update README with Teams Integration

**Files:**
- Modify: `README.md`

**Step 1: Add Teams section to README**

Add after the WhatsApp section:

```markdown
### Teams Bot (port 3978)

**POST /api/messages**
Microsoft Teams webhook endpoint (handled by Bot Framework).

**GET /health**
Health check endpoint.

## Teams Integration Setup

1. **Register Teams Bot:**
   - Go to Azure Portal → Azure Bot
   - Create new bot registration
   - Note the App ID and App Password
   - Enable Microsoft Teams channel

2. **Configure Webhook:**
   - Set messaging endpoint to: `https://your-domain.com/api/messages`
   - Update `.env` with App ID and Password

3. **Test Locally:**
   - Use ngrok: `ngrok http 3978`
   - Update webhook to ngrok URL
   - Test with Teams client
```

**Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add Teams integration setup instructions"
```

---

### Task 11: Create Teams Integration Guide

**Files:**
- Create: `docs/teams-setup.md`

**Step 1: Create comprehensive setup guide**

```markdown
# Microsoft Teams Integration Setup Guide

## Overview

This guide walks through setting up Microsoft Teams integration for NanoClaw.

## Prerequisites

- Microsoft Azure account
- Access to Microsoft Teams
- NanoClaw deployed with public URL (or ngrok for testing)

## Step 1: Register Bot in Azure

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to **Azure Bot** service
3. Click **Create**
4. Fill in:
   - Bot handle: `nanoclaw-bot`
   - Pricing tier: Standard (free tier available)
   - Type: Multi-Tenant
5. Click **Review + Create**
6. Note the **Microsoft App ID** from the created resource

## Step 2: Generate App Password

1. In your bot resource, go to **Configuration**
2. Click **Manage Password (Secret)**
3. Click **New client secret**
4. Give it a name and expiration
5. Copy the **Value** (this is your App Password)
   - ⚠️ Store this securely - you won't see it again!

## Step 3: Configure NanoClaw

Update `.env` file:

```bash
TEAMS_APP_ID=your-app-id-here
TEAMS_APP_PASSWORD=your-app-password-here
TEAMS_PORT=3978
```

## Step 4: Configure Webhook

### For Production:
1. Deploy NanoClaw with public URL
2. In Azure Bot → Configuration → Messaging endpoint
3. Set to: `https://your-domain.com/api/messages`

### For Testing (ngrok):
```bash
# Start ngrok
ngrok http 3978

# Note the https URL (e.g., https://abc123.ngrok.io)
# Update messaging endpoint to: https://abc123.ngrok.io/api/messages
```

## Step 5: Enable Teams Channel

1. In Azure Bot → Channels
2. Click **Microsoft Teams**
3. Accept Terms of Service
4. Click **Apply**

## Step 6: Test the Bot

1. In Teams, search for your bot by name
2. Start a conversation
3. Send: `help`
4. Submit a test case:

```
Test: Login validation
Scope: Authentication Module
Steps:
1. Navigate to /login
2. Enter invalid credentials
3. Verify error message
```

## Troubleshooting

### Bot not responding
- Check webhook URL is accessible
- Verify App ID and Password are correct
- Check logs: `docker logs nanoclaw-teams-bot`

### Authentication errors
- Regenerate App Password in Azure
- Update `.env` and restart container

### Timeout errors
- Ensure Agent API is running
- Check network connectivity between containers

## Security Considerations

- Keep App Password secure
- Use HTTPS for webhook endpoint
- Review bot permissions in Azure
- Monitor usage in Azure metrics
```

**Step 2: Commit**

```bash
git add docs/teams-setup.md
git commit -m "docs: add comprehensive Teams setup guide"
```

---

## Phase 4: Integration Testing

### Task 12: Create End-to-End Integration Test

**Files:**
- Create: `tests/integration/test_teams_e2e.py`

**Step 1: Write integration test**

```python
# tests/integration/test_teams_e2e.py
import pytest
from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop
from bot.teams_server import create_teams_server
from bot.conversation_manager import ConversationManager
from bot.agent_client import AgentAPIClient
from botbuilder.schema import Activity, ActivityTypes
import json


class TestTeamsE2E(AioHTTPTestCase):
    """End-to-end tests for Teams integration."""

    async def get_application(self):
        """Create test application with real components."""
        self.conversation_manager = ConversationManager()
        # Mock agent client for testing
        from unittest.mock import AsyncMock
        self.agent_client = AsyncMock(spec=AgentAPIClient)
        self.agent_client.submit_test_case.return_value = "job-test-123"
        self.agent_client.get_status.return_value = {
            "job_id": "job-test-123",
            "status": "completed",
            "test_case": {"name": "Test case"},
            "created_at": "2026-03-08T10:00:00Z"
        }

        app = await create_teams_server(
            app_id="test-id",
            app_password="test-password",
            conversation_manager=self.conversation_manager,
            agent_client=self.agent_client,
            port=3978
        )
        return app

    @unittest_run_loop
    async def test_submit_test_case_via_teams(self):
        """Test complete flow of submitting test case via Teams."""
        activity = Activity(
            type=ActivityTypes.message,
            text="""
Test: E2E Test
Scope: Integration
Steps:
1. Step one
2. Step two
""",
            from_property=type('obj', (object,), {'id': 'user-456'})()
        )

        # Create request payload
        payload = activity.serialize()

        resp = await self.client.post(
            "/api/messages",
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"}
        )

        assert resp.status in [200, 201]
        self.agent_client.submit_test_case.assert_called_once()

    @unittest_run_loop
    async def test_query_status_via_teams(self):
        """Test querying job status via Teams."""
        activity = Activity(
            type=ActivityTypes.message,
            text="status job-test-123",
            from_property=type('obj', (object,), {'id': 'user-456'})()
        )

        payload = activity.serialize()

        resp = await self.client.post(
            "/api/messages",
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"}
        )

        assert resp.status in [200, 201]
        self.agent_client.get_status.assert_called_once_with("job-test-123")
```

**Step 2: Run integration test**

Run: `pytest tests/integration/test_teams_e2e.py -v`
Expected: PASS - 2 tests

**Step 3: Commit**

```bash
git add tests/integration/test_teams_e2e.py
git commit -m "test: add Teams integration e2e tests"
```

---

### Task 13: Verify All Tests Pass

**Step 1: Run full test suite**

Run: `pytest -v`
Expected: All tests PASS

**Step 2: Run with coverage**

Run: `pytest --cov=bot --cov=agent --cov-report=term-missing`
Expected: Coverage report shows new Teams code covered

**Step 3: Create PR checklist**

Document in PR description:
- [x] Teams bot handler implemented
- [x] Message adapter created
- [x] Webhook server configured
- [x] Docker integration complete
- [x] Documentation updated
- [x] Integration tests passing

---

## Deployment Checklist

After completing all tasks:

1. **Build Docker images:**
   ```bash
   cd docker
   docker-compose build
   ```

2. **Start services:**
   ```bash
   docker-compose up -d
   ```

3. **Verify services:**
   ```bash
   curl http://localhost:3978/health
   ```

4. **Check logs:**
   ```bash
   docker logs nanoclaw-teams-bot
   ```

5. **Test with Teams client:**
   - Send message to bot
   - Verify response

---

**Plan Complete**

This plan implements Microsoft Teams integration with:
- Shared ConversationManager and AgentAPIClient
- Separate Teams bot container
- Message parsing and formatting
- Status queries
- Help documentation
- End-to-end tests
- Comprehensive setup guide
