# TestForge

Turn manual test cases into Playwright automation scripts in minutes.

TestForge is an AI-assisted testing platform that converts human test cases
into validated Playwright automation scripts.

Testers and Business Analysts can submit scenarios through WhatsApp or
Microsoft Teams, and TestForge automatically generates, validates, and
executes the tests—no coding required.

**The goal is simple:** remove the friction between manual test cases and
automated test execution.

## Why TestForge

Traditional test automation has three problems:

• **Writing automation scripts is slow** - Testers spend more time coding than testing
• **Test cases from BAs rarely get automated** - Business requirements stay manual
• **AI-generated tests often hallucinate** - Selectors fail, logic breaks, tests don't run

TestForge solves this by combining AI generation with structured validation
and Playwright execution.

**Key capabilities:**

✔ Convert natural language test cases into Playwright scripts
✔ Validate generated code before execution
✔ Integrate with collaboration tools (Teams / WhatsApp)
✔ Produce reusable test assets for CI pipelines
✔ Follow Registry-First architecture (no duplicate selectors)

## Quick Start

```bash
# 1. Clone and setup
git clone <repo>
cd testforge
./scripts/setup.sh

# The interactive CLI will guide you through:
# - Claude API key (required)
# - Agent and Bot settings (with defaults)
# - WhatsApp configuration (optional)
# - Microsoft Teams configuration (optional)
# - Docker settings (with defaults)

# 2. Start services
cd docker && docker-compose up

# Or run in background:
docker-compose up -d
```

### Running the Setup CLI Directly

You can also run the interactive setup CLI directly without the full setup script:

```bash
python3 scripts/setup_cli.py
```

This is useful if you want to reconfigure your environment or update specific settings.

### Setup Example

When you run `./scripts/setup.sh`, you'll see an interactive prompt:

```
🔧 TestForge Interactive Setup
==================================================

📝 Section 1/6: Claude API Configuration

Enter your Claude API key:
sk-ant-xxx...
✓ API key validated

⚙️  Section 2/6: Agent Settings

Agent host [0.0.0.0]: ⏎
Agent port [8000]: ⏎
...

================================
📋 Configuration Preview
================================
ANTHROPIC_API_KEY=sk-ant-...
AGENT_HOST=0.0.0.0
...

Write to .env? [Y/n]: Y
✅ Configuration written to .env
📁 Creating shared volume directories...
✅ Setup complete!
```

## Architecture

```
WhatsApp/Teams Users
    ↓
Bot Layer (WhatsApp/Teams interface)
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

### Teams Bot API (port 3978)

**POST /api/messages**
Webhook endpoint for Microsoft Teams bot framework. Receives messages from Teams channels and processes test case submissions.

**GET /health**
Health check endpoint for Teams bot service.

## Teams Integration Setup

TestForge supports Microsoft Teams as an additional interface for test case submission. See [docs/teams-setup.md](docs/teams-setup.md) for detailed setup instructions.

### Quick Overview

1. Register a bot in Azure Portal
2. Generate an App Password
3. Configure TestForge environment variables
4. Enable Teams channel in Azure
5. Test the bot in Teams

## Configuration

### Environment Variables

After running the setup script, your `.env` file will contain:

```bash
# Required
ANTHROPIC_API_KEY=sk-ant-xxx...

# Agent Settings (with defaults)
AGENT_HOST=0.0.0.0
AGENT_PORT=8000
SHARED_VOLUME_PATH=/testforge

# Bot Settings (with defaults)
BOT_HOST=0.0.0.0
BOT_PORT=5000
AGENT_API_URL=http://agent:8000

# WhatsApp (optional)
WHATSAPP_PHONE_NUMBER_ID=your_phone_id
WHATSAPP_ACCESS_TOKEN=your_access_token
WHATSAPP_WEBHOOK_VERIFY_TOKEN=your_verify_token

# Microsoft Teams (optional)
TEAMS_APP_ID=your_teams_app_id_here
TEAMS_APP_PASSWORD=your_teams_app_password_here
TEAMS_PORT=3978

# Docker (with defaults)
COMPOSE_PROJECT_NAME=testforge
```

### Updating Configuration

To update your configuration after initial setup:

1. Re-run the setup CLI: `python3 scripts/setup_cli.py`
2. Or edit `.env` directly (changes take effect on restart)
3. Restart services: `cd docker && docker-compose restart`

## Troubleshooting

### Setup Issues

**Problem:** Setup CLI fails to validate API key
- **Solution:** Ensure your API key starts with `sk-ant-` and is at least 20 characters

**Problem:** Port already in use
- **Solution:** Change the port number in the setup CLI or stop conflicting services

**Problem:** Docker build fails
- **Solution:** Ensure Docker is running and you have sufficient disk space

### Runtime Issues

**Problem:** Services not starting
- **Solution:** Check logs with `docker-compose logs` and verify `.env` configuration

**Problem:** Bot not receiving messages
- **Solution:** Verify webhook configuration and network connectivity

**Problem:** Agent not generating scripts
- **Solution:** Check ANTHROPIC_API_KEY is valid and has sufficient credits


## Directory Structure

```
testforge/
├── bot/              # Multi-platform bot service (WhatsApp/Teams)
├── agent/            # Agent sandbox service
├── shared/           # Docker volume mount
│   ├── ingress/      # Incoming test cases
│   ├── egress/       # Generated scripts
│   ├── page_objects/ # POM registry
│   └── manifest.json # Source of truth
├── docker/           # Container configurations
└── scripts/          # Setup and utility scripts
```

## Development

See `docs/plans/` for design and implementation details.

## License

Internal use only.
