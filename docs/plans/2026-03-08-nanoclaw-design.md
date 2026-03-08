# NanoClaw Design Document

**Date:** 2026-03-08
**Status:** Approved
**Version:** 1.0.0

---

## Executive Summary

NanoClaw is an internal QA automation tool that uses AI (Claude API) to generate Playwright test scripts from natural language test cases submitted via WhatsApp. The system follows a Registry-First architecture where the agent maintains a Page Object Model registry, extending it rather than creating duplicate code.

**Key Architectural Principles:**
- **Sandbox Boundary**: Agent operates in isolated Docker container with shared volume
- **Registry-First Logic**: Audit existing POM before generation, extend never duplicate
- **Validation Loop**: Self-correcting syntax and DOM validation before completion
- **Manifest as Source of Truth**: All state tracked in atomic manifest.json updates

---

## 1. Overall Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Team (WhatsApp Users)                       │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    WhatsApp Bot Container                        │
│  - WhatsApp Webhook Receiver (Twilio/Meta API)                  │
│  - Conversation State Manager                                   │
│  - File Parser (Markdown → Structured Test Case)                │
│  - Agent API Client                                             │
│  - Status/Manifest Reader                                       │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP API
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Agent Sandbox Container                      │
│  Shared Volume Mount: /nanoclaw                                 │
│    ├── ingress/           (Incoming test cases)                 │
│    ├── egress/            (Generated scripts)                   │
│    ├── page_objects/      (POM Registry)                        │
│    ├── html_dumps/        (DOM snapshots for validation)        │
│    ├── manifest.json      (Source of truth)                     │
│    └── logs/              (Agent activity logs)                 │
│                                                                 │
│  NanoClaw Agent Core:                                            │
│  - Registry Auditor (scans page_objects/)                       │
│  - Test Case Parser (structured NL → requirements)              │
│  - POM Expander (extends registry, never duplicates)            │
│  - Script Generator (Async Playwright Python)                   │
│  - Static Validator (syntax check)                              │
│  - DOM Validator (cross-reference locators)                     │
│  - Manifest Updater (atomic state updates)                      │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Component Design

### 2.1 WhatsApp Bot Container Components

**Language:** Python 3.11+ (async with `aiohttp`)

#### Webhook Receiver
```python
class WhatsAppWebhookReceiver:
    async def handle_incoming_message(self, payload: dict) -> None:
        # Extract phone_number, message_body, media_url
        # Route to Conversation Manager
```

#### Conversation State Manager
```python
@dataclass
class ConversationState:
    user_id: str
    state: Literal['idle', 'awaiting_test_case', 'processing', 'completed']
    test_case_draft: Optional[dict] = None
    current_job_id: Optional[str] = None

class ConversationManager:
    async def get_state(self, user_id: str) -> ConversationState
    async def update_state(self, user_id: str, state: ConversationState)
```

#### Test Case Parser
```python
@dataclass
class ParsedTestCase:
    name: str
    scope: str
    specs: List[str]
    steps: List[str]
    priority: str
    metadata: dict

class TestCaseParser:
    async def parse(self, text: str) -> ParsedTestCase
```

#### Agent API Client
```python
class AgentAPIClient:
    async def submit_test_case(self, test_case: ParsedTestCase) -> str
    async def get_status(self, job_id: str) -> dict
    async def get_generated_script(self, job_id: str) -> str
```

### 2.2 Agent Sandbox Container Components

**Language:** Python 3.11+ with Async Playwright

#### Registry Auditor
```python
@dataclass
class RegistryEntry:
    class_name: str
    file_path: str
    methods: List[str]
    selectors: dict
    last_modified: datetime

class RegistryAuditor:
    async def audit(self) -> Dict[str, RegistryEntry]
    async def find_existing_class(self, page_name: str) -> Optional[RegistryEntry]
    async def find_available_methods(self, class_name: str) -> List[str]
```

#### POM Expander
```python
class POMExpander:
    async def add_page_if_missing(self, page_name: str) -> None
    async def add_method_if_missing(self, page_name: str, method_name: str, selector: dict) -> None
    async def generate_page_object(self, page_name: str, elements: List[ElementDefinition]) -> str
```

#### Script Generator
```python
class ScriptGenerator:
    async def generate_test_script(self, test_case: ParsedTestCase, registry: Dict[str, RegistryEntry]) -> str

    def _generate_imports(self) -> str:
        return \"\"\"import asyncio
from playwright.async_api import async_playwright, Page, expect
from page_objects.login_page import LoginPage
\"\"\"
```

#### Static Validator
```python
class StaticValidator:
    async def validate_syntax(self, script_path: str) -> ValidationResult
```

#### DOM Validator
```python
class DOMValidator:
    async def validate_locators(self, script_path: str, html_dumps: Dict[str, str]) -> ValidationResult
```

#### Manifest Manager
```python
@dataclass
class ManifestEntry:
    job_id: str
    status: Literal['pending', 'processing', 'completed', 'failed']
    test_case: ParsedTestCase
    generated_script: Optional[str] = None
    page_objects_created: List[str] = field(default_factory=list)
    validation_result: Optional[dict] = None
    error_message: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

class ManifestManager:
    async def create_job(self, test_case: ParsedTestCase) -> str
    async def update_job_status(self, job_id: str, status: str, **kwargs) -> None
    async def get_job(self, job_id: str) -> Optional[ManifestEntry]
```

---

## 3. Data Flow

### 3.1 End-to-End Flow

1. **Test Case Submission (WhatsApp)**
   - User sends structured test case via WhatsApp
   - Bot parses and validates format
   - Bot submits to Agent API

2. **Registry Audit (Agent)**
   - Agent creates job in manifest.json
   - RegistryAuditor scans page_objects/
   - Builds internal registry map

3. **POM Expansion (Registry-First)**
   - ScriptGenerator checks registry for existing classes
   - POMExpander adds missing methods to existing classes
   - Updates manifest with created/modified page objects

4. **Script Generation**
   - ScriptGenerator generates async Playwright script
   - Uses registry methods when available
   - Outputs to egress/{job_id}/

5. **Validation Loop**
   - StaticValidator: Syntax check + self-patch (max 3 attempts)
   - DOMValidator: Cross-reference selectors against HTML dumps
   - Updates manifest with results

6. **Notification (WhatsApp)**
   - Bot polls for job completion
   - Sends user download link or error details

### 3.2 Directory Structure

```
nanoclaw/
├── docker/
│   ├── Dockerfile.bot
│   ├── Dockerfile.agent
│   └── docker-compose.yml
│
├── bot/
│   ├── bot/
│   │   ├── webhook_receiver.py
│   │   ├── conversation_manager.py
│   │   ├── test_case_parser.py
│   │   ├── agent_client.py
│   │   ├── message_formatter.py
│   │   └── main.py
│   ├── tests/bot/
│   ├── requirements.txt
│   └── README.md
│
├── agent/
│   ├── agent/
│   │   ├── registry_auditor.py
│   │   ├── pom_expander.py
│   │   ├── script_generator.py
│   │   ├── static_validator.py
│   │   ├── dom_validator.py
│   │   ├── manifest_manager.py
│   │   ├── api.py
│   │   └── main.py
│   ├── tests/agent/
│   ├── requirements.txt
│   └── README.md
│
├── shared/                      # Docker Volume Mount
│   ├── ingress/{job_id}/test_case.json
│   ├── egress/{job_id}/test_*.py
│   ├── page_objects/*.py
│   ├── html_dumps/*.html
│   ├── manifest.json
│   └── logs/*.log
│
├── docs/plans/2026-03-08-nanoclaw-design.md
├── .env.example
├── .gitignore
└── README.md
```

### 3.3 Manifest.json Structure

```json
{
  "version": "1.0.0",
  "last_updated": "2026-03-08T15:30:00Z",
  "statistics": {
    "total_jobs": 42,
    "completed": 38,
    "failed": 2,
    "pending": 2
  },
  "jobs": [
    {
      "job_id": "uuid",
      "status": "completed",
      "test_case": {
        "name": "Login with invalid credentials",
        "scope": "Authentication Module",
        "specs": ["Verify error message appears"],
        "steps": ["Navigate to /login", "Enter invalid email"],
        "priority": "P0",
        "metadata": {"author": "john.doe"}
      },
      "generated_script": "egress/{job_id}/test_login_invalid.py",
      "page_objects_created": ["login_page.py:added_get_error_message"],
      "validation_result": {"syntax": "pass", "dom_validation": "pass"},
      "created_at": "2026-03-08T15:00:00Z",
      "completed_at": "2026-03-08T15:02:30Z"
    }
  ]
}
```

---

## 4. Error Handling

### Error Hierarchy

| Level | Error Type | Response |
|-------|-----------|----------|
| **1 - Bot** | Invalid format | WhatsApp: "Please include: Test name, Scope, Steps" |
| **1 - Bot** | Agent unreachable | WhatsApp: "Agent down. Job queued: {job_id}" |
| **1 - Bot** | Job timeout | WhatsApp: "Taking longer than expected..." |
| **1 - Bot** | Validation failure | WhatsApp: "Validation failed. Download: {url}" |
| **2 - Agent** | Syntax error | Auto-patch (max 3 attempts) |
| **2 - Agent** | Missing DOM | Warning, allow manual review |
| **2 - Agent** | Registry conflict | Detect before generation, ask human |
| **2 - Agent** | POM expansion fail | Fallback: inline selectors + log debt |
| **2 - Agent** | Manifest conflict | Atomic write (temp + rename), retry |
| **3 - Critical** | API rate limit | Queue job, WhatsApp: "Queued, 5min delay" |
| **3 - Critical** | Volume corruption | Alert admin, pause jobs, restore backup |
| **3 - Critical** | Disk full | Alert admin, auto-cleanup old egress/ |
| **3 - Critical** | Security exception | Fail immediately, alert admin, audit log |

---

## 5. Testing Strategy

### Unit Tests (pytest + pytest-asyncio)

- **RegistryAuditor**: Scan, detect conflicts, index methods (90%+ coverage)
- **POMExpander**: Add page, add method, prevent duplicates (85%+ coverage)
- **ScriptGenerator**: Generate async script, use registry (90%+ coverage)
- **StaticValidator**: Parse, patch, retry logic (95%+ coverage)
- **DOMValidator**: Extract selectors, cross-reference DOM (85%+ coverage)
- **ManifestManager**: Atomic write, read, update status (90%+ coverage)
- **ConversationManager**: Multi-turn state, timeout handling (80%+ coverage)
- **TestCaseParser**: Parse structured NL, validation (85%+ coverage)

### Integration Tests

- Full flow: Test case submission → Script generation → Validation
- Bot-Agent API communication
- Manifest atomic updates under concurrent load

---

## 6. Technology Stack

| Component | Technology |
|-----------|------------|
| **Bot Container** | Python 3.11+, aiohttp, WhatsApp Business API |
| **Agent Container** | Python 3.11+, FastAPI, Async Playwright |
| **AI** | Claude API (Anthropic) |
| **Orchestration** | Docker Compose (local), potential Kubernetes (prod) |
| **Volume Storage** | Docker named volume or bind mount |
| **Testing** | pytest, pytest-asyncio, pytest-cov |

---

## 7. Success Criteria

1. **Functional**
   - Bot receives WhatsApp messages and parses test cases
   - Agent generates async Playwright scripts with 90%+ syntactic validity
   - Registry-First logic prevents duplicate POM code
   - Manifest accurately tracks all job states

2. **Quality**
   - 85%+ test coverage across critical paths
   - Zero syntax errors in generated scripts (after validation loop)
   - Sub-5 second response time for status queries
   - Graceful handling of all error levels

3. **Usability**
   - Team can submit test case via WhatsApp in <2 minutes
   - Generated scripts are ready to run (no manual fixes needed for standard cases)
   - Clear error messages guide users to correct format

---

## 8. Next Steps

1. **Phase 1**: Scaffold project structure, setup Docker containers
2. **Phase 2**: Implement core Agent components (Registry, Generator, Validator)
3. **Phase 3**: Implement Bot components (Webhook, Parser, Conversation)
4. **Phase 4**: Integration testing and end-to-end validation
5. **Phase 5**: WhatsApp Business API integration and deployment

---

**Design Approved By:** Team
**Date Approved:** 2026-03-08
**Implementation Plan:** See 2026-03-08-nanoclaw-implementation.md
