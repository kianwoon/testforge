# NanoClow

AI-driven Playwright test generation via WhatsApp.

## What is NanoClow?

NanoClow is an internal QA automation tool that:
- Accepts test cases via structured natural language
- Uses AI (Claude) to generate async Playwright Python scripts
- Follows Registry-First architecture (extends POM, never duplicates)
- Validates scripts with syntax checking and DOM cross-reference
- Notifies team via WhatsApp when scripts are ready

## Quick Start

```bash
# 1. Clone and setup
git clone <repo>
cd nanoclaw
./scripts/setup.sh

# 2. Configure environment
nano .env  # Add your Claude API key and WhatsApp credentials

# 3. Start services
cd docker && docker-compose up

# Or run in background:
docker-compose up -d
```

## Architecture

```
WhatsApp Users
    ↓
WhatsApp Bot (interface layer)
    ↓ HTTP API
Agent Sandbox (generator)
    ↓
Shared Volume (manifest.json, page_objects/, egress/)
```

## API Endpoints

### Agent API (port 8000)

**POST /api/v1/submit**
Submit a test case for processing.

```json
{
  "name": "Login with invalid credentials",
  "scope": "Authentication Module",
  "specs": ["Verify error message"],
  "steps": [
    "Navigate to /login",
    "Enter invalid email",
    "Click login"
  ],
  "priority": "P0"
}
```

**GET /api/v1/status/{job_id}**
Get job status and details.

### Bot API (port 5000)

**GET /health**
Health check endpoint.

## Directory Structure

```
nanoclaw/
├── bot/              # WhatsApp bot service
├── agent/            # Agent sandbox service
├── shared/           # Docker volume mount
│   ├── ingress/      # Incoming test cases
│   ├── egress/       # Generated scripts
│   ├── page_objects/ # POM registry
│   └── manifest.json # Source of truth
└── docker/           # Container configurations
```

## Development

See `docs/plans/` for design and implementation details.

## License

Internal use only.
