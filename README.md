# NanoClow

AI-driven Playwright test generation via WhatsApp.

## Quick Start

```bash
cp .env.example .env
# Edit .env with your API keys
docker-compose up --build
```

## Architecture

- **Bot Container**: WhatsApp webhook receiver and conversation manager
- **Agent Container**: AI-powered test script generator with Registry-First POM
- **Shared Volume**: Persistent state (manifest.json, page_objects, egress)

## Development

See `docs/plans/` for design and implementation details.
