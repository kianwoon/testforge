# bot/bot/teams_main.py
import asyncio
import logging
import os
from bot.teams_server import create_teams_server
from bot.conversation_manager import ConversationManager
from bot.agent_client import AgentAPIClient
from aiohttp import web

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

    # Run the web server
    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(runner, "0.0.0.0", teams_port)
    await site.start()

    logger.info(f"Teams bot server running on port {teams_port}")

    # Keep server running
    try:
        while True:
            await asyncio.sleep(3600)
    except KeyboardInterrupt:
        logger.info("Shutting down Teams bot server...")
        await runner.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
