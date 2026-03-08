import asyncio
from aiohttp import web
from dotenv import load_dotenv

load_dotenv()

async def health_check(request: web.Request) -> web.Response:
    return web.json_response({"status": "healthy", "service": "bot"})

async def create_app() -> web.Application:
    app = web.Application()
    app.router.add_get("/health", health_check)
    return app

if __name__ == "__main__":
    app = asyncio.run(create_app())
    web.run_app(app, host="0.0.0.0", port=5000)
