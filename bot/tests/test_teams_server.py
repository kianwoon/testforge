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

    @unittest_run_loop
    async def test_health_endpoint_returns_json(self):
        """Test health endpoint returns proper JSON response."""
        resp = await self.client.get("/health")
        assert resp.status == 200
        data = await resp.json()
        assert isinstance(data, dict)
        assert "status" in data
        assert "service" in data

    @unittest_run_loop
    async def test_invalid_endpoint_returns_404(self):
        """Test that invalid endpoints return 404."""
        resp = await self.client.get("/invalid-endpoint")
        assert resp.status == 404

    @unittest_run_loop
    async def test_health_endpoint_get_only(self):
        """Test that health endpoint accepts GET requests."""
        # GET should work
        resp = await self.client.get("/health")
        assert resp.status == 200

    @unittest_run_loop
    async def test_messages_endpoint_post_only(self):
        """Test that messages endpoint accepts POST requests."""
        # POST should be processed (even if auth fails)
        resp = await self.client.post("/api/messages", data="{}")
        assert resp.status != 405  # Method not allowed

        # GET should fail
        resp = await self.client.get("/api/messages")
        assert resp.status == 405  # Method not allowed
