# bot/bot/teams_server.py
import logging
from aiohttp import web
from botbuilder.core import BotFrameworkAdapter, BotFrameworkAdapterSettings
from botbuilder.integration.aiohttp import aiohttp_channel_service
from .teams_bot import NanoClawTeamsBot
from .conversation_manager import ConversationManager
from .agent_client import AgentAPIClient

logger = logging.getLogger(__name__)


async def create_teams_server(
    app_id: str,
    app_password: str,
    conversation_manager: ConversationManager,
    agent_client: AgentAPIClient,
    port: int = 3978
) -> web.Application:
    """
    Create and configure the Teams webhook server.

    Args:
        app_id: Microsoft Teams Bot App ID
        app_password: Microsoft Teams Bot App Password
        conversation_manager: Manager for conversation state
        agent_client: Client for Agent API communication
        port: Port to run the server on (default: 3978)

    Returns:
        Configured aiohttp Application instance
    """
    # Create adapter settings
    settings = BotFrameworkAdapterSettings(
        app_id=app_id,
        app_password=app_password
    )

    # Create adapter
    adapter = BotFrameworkAdapter(settings)

    # Create bot instance
    bot = NanoClawTeamsBot(
        conversation_manager=conversation_manager,
        agent_client=agent_client
    )

    # Create web application
    app = web.Application()

    # Health check endpoint
    async def health_check(request: web.Request) -> web.Response:
        """Health check endpoint."""
        return web.json_response({
            "status": "healthy",
            "service": "teams-bot"
        })

    # Messages endpoint
    async def messages(request: web.Request) -> web.Response:
        """
        Handle incoming messages from Microsoft Teams.

        This endpoint receives activities from Teams via the Bot Framework.
        """
        # Delegate to the adapter which handles auth and routing
        return await aiohttp_channel_service(adapter, bot, request)

    # Register routes
    app.router.add_get("/health", health_check)
    app.router.add_post("/api/messages", messages)

    logger.info(f"Teams webhook server configured on port {port}")

    return app
