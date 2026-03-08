# Interactive Setup CLI Implementation Plan

> **Goal:** Create an interactive `/setup` command that guides users through configuration without manual .env editing

**Approach:** Python-based interactive CLI with input validation, defaults, and smart prompts

---

## Architecture

```
User runs: python scripts/setup_cli.py (or ./setup)
    ↓
Interactive CLI prompts for each config section
    ↓
[Optional] Skip sections with ENTER (uses defaults)
    ↓
Validates inputs (not empty, proper format)
    ↓
Shows preview before writing .env
    ↓
Writes .env file and confirms completion
```

---

## Configuration Sections

### Section 1: Claude API (Required)
- `ANTHROPIC_API_KEY` - API key for Claude
- Validation: Not empty, starts with `sk-ant-`

### Section 2: Agent Settings (Defaults provided)
- `AGENT_HOST` - Default: `0.0.0.0`
- `AGENT_PORT` - Default: `8000`
- `SHARED_VOLUME_PATH` - Default: `/nanoclaw`

### Section 3: Bot Settings (Defaults provided)
- `BOT_HOST` - Default: `0.0.0.0`
- `BOT_PORT` - Default: `5000`
- `AGENT_API_URL` - Default: `http://agent:8000`

### Section 4: WhatsApp (Optional)
- `WHATSAPP_PHONE_NUMBER_ID`
- `WHATSAPP_ACCESS_TOKEN`
- `WHATSAPP_WEBHOOK_VERIFY_TOKEN`
- Can skip entire section

### Section 5: Microsoft Teams (Optional)
- `TEAMS_APP_ID`
- `TEAMS_APP_PASSWORD`
- `TEAMS_PORT` - Default: `3978`
- Can skip entire section

### Section 6: Docker (Defaults provided)
- `COMPOSE_PROJECT_NAME` - Default: `nanoclaw`

---

## Implementation Plan

### Task 1: Add Teams config to .env.example
**File:** `.env.example`
- Add Teams configuration section (was missing after merge)

### Task 2: Create setup_cli.py
**File:** `scripts/setup_cli.py`
- Interactive prompts using `input()` with validation
- Color-coded sections for readability
- Skip option with ENTER key
- Preview before write

### Task 3: Update setup.sh
**File:** `scripts/setup.sh`
- Replace manual .env copy with Python CLI call
- Keep directory creation and docker build

### Task 4: Create setup tests
**File:** `tests/test_setup_cli.py`
- Test interactive prompts (mock inputs)
- Test validation logic
- Test .env file writing

### Task 5: Update README
**File:** `README.md`
- Add quick setup instructions with example output

---

## Example Output

```bash
$ python scripts/setup_cli.py

🔧 NanoClow Interactive Setup
================================

Section 1/6: Claude API Configuration

ANTHROPIC_API_KEY (required):
Enter your Claude API key [sk-ant-...]: ********************************
✓ API key validated

Section 2/6: Agent Settings

AGENT_HOST [0.0.0.0]: ⏎
AGENT_PORT [8000]: ⏎
SHARED_VOLUME_PATH [/nanoclaw]: ⏎

Section 3/6: Bot Settings

BOT_HOST [0.0.0.0]: ⏎
BOT_PORT [5000]: ⏎
AGENT_API_URL [http://agent:8000]: ⏎

Section 4/6: WhatsApp Configuration (optional)
Press ENTER to skip this section...
⏎

Section 5/6: Microsoft Teams Configuration (optional)
TEAMS_APP_ID (optional):
⏎

Section 6/6: Docker Settings

COMPOSE_PROJECT_NAME [nanoclaw]: ⏎

================================
📋 Configuration Preview
================================
ANTHROPIC_API_KEY=sk-ant-...
AGENT_HOST=0.0.0.0
AGENT_PORT=8000
SHARED_VOLUME_PATH=/nanoclaw
...

Write to .env? [Y/n]: Y

✅ Configuration written to .env
📁 Creating shared volume directories...
✅ Setup complete!

To start NanoClow:
  cd docker && docker-compose up
```

---

## Features

✅ **Smart Prompts**
- Show current value if .env exists
- Allow keeping current value with ENTER
- Clear labels showing defaults

✅ **Input Validation**
- Required fields can't be empty
- Format validation (API keys, ports, URLs)
- Clear error messages

✅ **Skip Optional Sections**
- Press ENTER to skip WhatsApp config
- Press ENTER to skip Teams config
- Only required: Claude API key

✅ **Preview Before Write**
- Shows all values before writing
- Confirmation step prevents accidents

✅ **User-Friendly**
- Color-coded sections
- Progress indicator (1/6)
- Clear success/error messages

---

## Implementation Details

### setup_cli.py Structure

```python
#!/usr/bin/env python3
import os
import sys
from pathlib import Path

class ConfigSetup:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.env_file = self.project_root / ".env"
        self.env_example = self.project_root / ".env.example"
        self.config = {}

    def run(self):
        self.print_header()
        self.setup_sections()
        self.preview_and_write()
        self.create_directories()

    def prompt_required(self, key, description, validator=None):
        # Prompt with validation

    def prompt_optional(self, key, description, default=None):
        # Prompt that can be skipped

    def print_header(self):
        # Show welcome banner

    def setup_sections(self):
        # Run through each section
```

---

## Success Criteria

- [x] Interactive prompts with validation
- [x] Support for defaults and skipping
- [x] Preview before writing
- [x] Tests for validation logic
- [x] Updated README with new setup flow
- [ ] All tests passing

---

**Ready to implement?** This plan creates a much better onboarding experience for NanoClow users.
