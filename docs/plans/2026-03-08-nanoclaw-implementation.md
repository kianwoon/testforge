# NanoClow Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a WhatsApp-driven QA automation tool that generates Playwright test scripts using AI, following Registry-First architecture with isolated Docker containers.

**Architecture:** Hybrid system with WhatsApp Bot (interface) and Agent Sandbox (generator) communicating via HTTP API, sharing state through Docker volume mount.

**Tech Stack:** Python 3.11+, Async Playwright, FastAPI (Agent), aiohttp (Bot), Docker, WhatsApp Business API, Claude API

---

## Phase 1: Project Scaffold & Docker Foundation

### Task 1: Create Project Directory Structure

**Files:**
- Create: `docker/`, `bot/`, `agent/`, `shared/`, `docs/`, `tests/`
- Create: `.env.example`, `.gitignore`, `README.md`

**Step 1: Create directory structure**

```bash
mkdir -p docker bot/bot bot/tests agent/agent agent/tests shared/{ingress,egress,page_objects,html_dumps,logs} docs/plans tests
```

**Step 2: Create .gitignore**

```bash
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
.venv/

# NanoClow
shared/egress/*
shared/ingress/*
!shared/egress/.gitkeep
!shared/ingress/.gitkeep
.env

# IDE
.vscode/
.idea/
*.swp

# Logs
*.log
shared/logs/*
EOF
```

**Step 3: Create .env.example**

```bash
cat > .env.example << 'EOF'
# Claude API
ANTHROPIC_API_KEY=your_api_key_here

# Agent Settings
AGENT_HOST=0.0.0.0
AGENT_PORT=8000
SHARED_VOLUME_PATH=/nanoclaw

# Bot Settings
BOT_HOST=0.0.0.0
BOT_PORT=5000
AGENT_API_URL=http://agent:8000

# WhatsApp Business API
WHATSAPP_PHONE_NUMBER_ID=your_phone_id
WHATSAPP_ACCESS_TOKEN=your_access_token
WHATSAPP_WEBHOOK_VERIFY_TOKEN=your_verify_token

# Docker
COMPOSE_PROJECT_NAME=nanoclaw
EOF
```

**Step 4: Create README.md**

```bash
cat > README.md << 'EOF'
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
EOF
```

**Step 5: Commit**

```bash
git add .
git commit -m "feat: scaffold project structure

- Create directory layout for bot, agent, shared volume
- Add .env.example with all required configuration
- Add .gitignore and README.md"
```

---

### Task 2: Create Docker Configuration

**Files:**
- Create: `docker/Dockerfile.bot`
- Create: `docker/Dockerfile.agent`
- Create: `docker/docker-compose.yml`

**Step 1: Write Dockerfile.bot**

```bash
cat > docker/Dockerfile.bot << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY bot/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY bot/ /app/

# Expose port
EXPOSE 5000

# Run application
CMD ["python", "-m", "bot.main"]
EOF
```

**Step 2: Write Dockerfile.agent**

```bash
cat > docker/Dockerfile.agent << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for Playwright
RUN apt-get update && apt-get install -y \
    gcc \
    libnss3 \
    libnspr4 \
    libdbus-1-3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY agent/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install chromium

# Copy application
COPY agent/ /app/

# Create shared volume directories
RUN mkdir -p /nanoclaw/{ingress,egress,page_objects,html_dumps,logs}

# Expose port
EXPOSE 8000

# Run application
CMD ["python", "-m", "agent.main"]
EOF
```

**Step 3: Write docker-compose.yml**

```bash
cat > docker/docker-compose.yml << 'EOF'
version: '3.8'

services:
  agent:
    build:
      context: ..
      dockerfile: docker/Dockerfile.agent
    container_name: nanoclaw-agent
    volumes:
      - ../shared:/nanoclaw
    ports:
      - "8000:8000"
    env_file:
      - ../.env
    environment:
      - PYTHONUNBUFFERED=1
    restart: unless-stopped

  bot:
    build:
      context: ..
      dockerfile: docker/Dockerfile.bot
    container_name: nanoclaw-bot
    depends_on:
      - agent
    ports:
      - "5000:5000"
    env_file:
      - ../.env
    environment:
      - PYTHONUNBUFFERED=1
    restart: unless-stopped

volumes:
  shared_volume:
EOF
```

**Step 4: Commit**

```bash
git add docker/
git commit -m "feat: add Docker configuration

- Add Dockerfile for bot container (Python 3.11)
- Add Dockerfile for agent container (with Playwright dependencies)
- Add docker-compose.yml for local development"
```

---

### Task 3: Create Bot Requirements and Basic Structure

**Files:**
- Create: `bot/requirements.txt`
- Create: `bot/bot/__init__.py`
- Create: `bot/bot/main.py`
- Create: `bot/tests/__init__.py`

**Step 1: Write bot/requirements.txt**

```bash
cat > bot/requirements.txt << 'EOF'
aiohttp==3.9.1
aiofiles==23.2.1
python-dotenv==1.0.0
pydantic==2.5.3
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
EOF
```

**Step 2: Create bot package init**

```bash
touch bot/bot/__init__.py
```

**Step 3: Write bot/bot/main.py (basic skeleton)**

```bash
cat > bot/bot/main.py << 'EOF'
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
EOF
```

**Step 4: Commit**

```bash
git add bot/
git commit -m "feat: add bot basic structure

- Add requirements.txt with aiohttp, pydantic, pytest
- Add basic Flask skeleton with health check endpoint"
```

---

### Task 4: Create Agent Requirements and Basic Structure

**Files:**
- Create: `agent/requirements.txt`
- Create: `agent/agent/__init__.py`
- Create: `agent/agent/main.py`
- Create: `agent/tests/__init__.py`

**Step 1: Write agent/requirements.txt**

```bash
cat > agent/requirements.txt << 'EOF'
fastapi==0.109.0
uvicorn[standard]==0.27.0
pydantic==2.5.3
anthropic==0.18.1
playwright==1.40.0
aiofiles==23.2.1
python-dotenv==1.0.0
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
httpx==0.26.0
EOF
```

**Step 2: Create agent package init**

```bash
touch agent/agent/__init__.py
```

**Step 3: Write agent/agent/main.py (basic skeleton)**

```bash
cat > agent/agent/main.py << 'EOF'
import asyncio
from fastapi import FastAPI
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="NanoClow Agent")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "agent"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
EOF
```

**Step 4: Commit**

```bash
git add agent/
git commit -m "feat: add agent basic structure

- Add requirements.txt with FastAPI, Playwright, Anthropic
- Add basic FastAPI skeleton with health check endpoint"
```

---

## Phase 2: Shared Data Models

### Task 5: Create Shared Pydantic Models

**Files:**
- Create: `shared/models.py` (conceptual - will be duplicated in bot/agent)
- Create: `bot/bot/models.py`
- Create: `agent/agent/models.py`

**Step 1: Write bot/bot/models.py**

```bash
cat > bot/bot/models.py << 'EOF'
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime
from enum import Enum

class ConversationState(str, Enum):
    IDLE = "idle"
    AWAITING_TEST_CASE = "awaiting_test_case"
    PROCESSING = "processing"
    COMPLETED = "completed"

class TestCaseSpec(BaseModel):
    name: str = Field(..., description="Test case name")
    scope: str = Field(..., description="Module/feature being tested")
    specs: List[str] = Field(default_factory=list, description="Specific requirements to verify")
    steps: List[str] = Field(..., description="Test execution steps")
    priority: str = Field(default="P1", description="Priority level (P0, P1, P2)")
    metadata: dict = Field(default_factory=dict)

class ConversationData(BaseModel):
    user_id: str
    state: ConversationState
    test_case_draft: Optional[TestCaseSpec] = None
    current_job_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class JobStatus(BaseModel):
    job_id: str
    status: Literal["pending", "processing", "completed", "failed"]
    created_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
EOF
```

**Step 2: Write agent/agent/models.py**

```bash
cat > agent/agent/models.py << 'EOF'
from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict, Any
from datetime import datetime
from enum import Enum

class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class TestCaseSpec(BaseModel):
    name: str
    scope: str
    specs: List[str]
    steps: List[str]
    priority: str = "P1"
    metadata: Dict[str, Any] = Field(default_factory=dict)

class RegistryEntry(BaseModel):
    class_name: str
    file_path: str
    methods: List[str]
    selectors: Dict[str, str] = Field(default_factory=dict)
    last_modified: Optional[datetime] = None

class ManifestEntry(BaseModel):
    job_id: str
    status: JobStatus
    test_case: TestCaseSpec
    generated_script: Optional[str] = None
    page_objects_created: List[str] = Field(default_factory=list)
    validation_result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

class Manifest(BaseModel):
    version: str = "1.0.0"
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    statistics: Dict[str, int] = Field(
        default_factory=lambda: {"total_jobs": 0, "completed": 0, "failed": 0, "pending": 0}
    )
    jobs: List[ManifestEntry] = Field(default_factory=list)
EOF
```

**Step 3: Commit**

```bash
git add bot/bot/models.py agent/agent/models.py
git commit -m "feat: add shared data models

- Add Pydantic models for test cases, conversations, jobs
- Define manifest structure for agent
- Define conversation state for bot"
```

---

## Phase 3: Agent Core Components

### Task 6: Implement Manifest Manager

**Files:**
- Create: `agent/agent/manifest_manager.py`

**Step 1: Write failing test**

```bash
cat > agent/tests/test_manifest_manager.py << 'EOF'
import pytest
import tempfile
from pathlib import Path
from agent.manifest_manager import ManifestManager
from agent.models import TestCaseSpec, JobStatus

@pytest.mark.asyncio
async def test_create_job_creates_unique_id():
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = ManifestManager(shared_volume_path=tmpdir)

        test_case = TestCaseSpec(
            name="Test login",
            scope="Auth",
            steps=["Step 1"]
        )

        job_id1 = await manager.create_job(test_case)
        job_id2 = await manager.create_job(test_case)

        assert job_id1 != job_id2
        assert len(job_id1) == 36  # UUID4 format

@pytest.mark.asyncio
async def test_update_job_status():
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = ManifestManager(shared_volume_path=tmpdir)

        test_case = TestCaseSpec(
            name="Test login",
            scope="Auth",
            steps=["Step 1"]
        )

        job_id = await manager.create_job(test_case)
        await manager.update_job_status(job_id, JobStatus.COMPLETED)

        job = await manager.get_job(job_id)
        assert job.status == JobStatus.COMPLETED
        assert job.completed_at is not None
EOF
```

**Step 2: Run test to verify it fails**

```bash
cd agent && python -m pytest tests/test_manifest_manager.py -v 2>&1 || true
# Expected: ModuleNotFoundError or import errors
```

**Step 3: Write minimal implementation**

```bash
cat > agent/agent/manifest_manager.py << 'EOF'
import json
import uuid
from pathlib import Path
from datetime import datetime
from typing import Optional
import aiofiles
from .models import ManifestEntry, Manifest, TestCaseSpec, JobStatus

class ManifestManager:
    def __init__(self, shared_volume_path: str = "/nanoclaw"):
        self.shared_volume = Path(shared_volume_path)
        self.manifest_path = self.shared_volume / "manifest.json"
        self._lock = None

    async def _load_manifest(self) -> Manifest:
        if not self.manifest_path.exists():
            return Manifest()

        async with aiofiles.open(self.manifest_path, 'r') as f:
            data = json.loads(await f.read())
            return Manifest(**data)

    async def _save_manifest(self, manifest: Manifest) -> None:
        # Atomic write: temp file + rename
        temp_path = self.manifest_path.with_suffix('.tmp')
        manifest.last_updated = datetime.utcnow()

        async with aiofiles.open(temp_path, 'w') as f:
            await f.write(manifest.model_dump_json(indent=2))

        temp_path.rename(self.manifest_path)

    async def create_job(self, test_case: TestCaseSpec) -> str:
        manifest = await self._load_manifest()

        job_id = str(uuid.uuid4())
        entry = ManifestEntry(
            job_id=job_id,
            status=JobStatus.PENDING,
            test_case=test_case
        )

        manifest.jobs.append(entry)
        manifest.statistics["total_jobs"] += 1
        manifest.statistics["pending"] += 1

        await self._save_manifest(manifest)
        return job_id

    async def update_job_status(
        self,
        job_id: str,
        status: JobStatus,
        **kwargs
    ) -> None:
        manifest = await self._load_manifest()

        for job in manifest.jobs:
            if job.job_id == job_id:
                old_status = job.status
                job.status = status

                if status == JobStatus.COMPLETED:
                    job.completed_at = datetime.utcnow()
                    manifest.statistics["completed"] += 1
                    manifest.statistics["pending"] -= 1
                elif status == JobStatus.FAILED:
                    manifest.statistics["failed"] += 1
                    manifest.statistics["pending"] -= 1

                for key, value in kwargs.items():
                    setattr(job, key, value)

                break

        await self._save_manifest(manifest)

    async def get_job(self, job_id: str) -> Optional[ManifestEntry]:
        manifest = await self._load_manifest()

        for job in manifest.jobs:
            if job.job_id == job_id:
                return job

        return None
EOF
```

**Step 4: Run test to verify it passes**

```bash
cd agent && python -m pytest tests/test_manifest_manager.py -v
# Expected: PASS
```

**Step 5: Commit**

```bash
git add agent/agent/manifest_manager.py agent/tests/test_manifest_manager.py
git commit -m "feat: implement ManifestManager

- Add atomic manifest.json operations (temp file + rename)
- Implement job creation, status updates, retrieval
- Track statistics (total, completed, failed, pending)"
```

---

### Task 7: Implement Registry Auditor

**Files:**
- Create: `agent/agent/registry_auditor.py`
- Create: `shared/page_objects/base_page.py` (for testing)
- Create: `shared/page_objects/__init__.py`

**Step 1: Create test fixtures**

```bash
cat > shared/page_objects/__init__.py << 'EOF'
from .base_page import BasePage
EOF

cat > shared/page_objects/base_page.py << 'EOF'
from playwright.async_api import Page

class BasePage:
    def __init__(self, page: Page):
        self.page = page
EOF

cat > shared/page_objects/sample_page.py << 'EOF'
from playwright.async_api import Page, Locator
from .base_page import BasePage

class SamplePage(BasePage):
    async def goto(self):
        await self.page.goto("/sample")

    async def click_button(self) -> None:
        button = self.page.get_by_role("button", name="Submit")
        await button.click()

    async def get_error_message(self) -> Locator:
        return self.page.get_by_role("alert", name="Error")
EOF
```

**Step 2: Write failing test**

```bash
cat > agent/tests/test_registry_auditor.py << 'EOF'
import pytest
import tempfile
from pathlib import Path
from agent.registry_auditor import RegistryAuditor

@pytest.mark.asyncio
async def test_audit_scans_page_objects():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Copy sample page object
        po_dir = Path(tmpdir) / "page_objects"
        po_dir.mkdir()

        # Write sample page
        (po_dir / "sample_page.py").write_text('''
from playwright.async_api import Page, Locator
from .base_page import BasePage

class SamplePage(BasePage):
    async def goto(self):
        await self.page.goto("/sample")
''')

        auditor = RegistryAuditor(page_objects_path=str(po_dir))
        registry = await auditor.audit()

        assert "SamplePage" in registry
        assert registry["SamplePage"].file_path == "sample_page.py"
        assert "goto" in registry["SamplePage"].methods

@pytest.mark.asyncio
async def test_find_existing_class():
    with tempfile.TemporaryDirectory() as tmpdir:
        po_dir = Path(tmpdir) / "page_objects"
        po_dir.mkdir()
        (po_dir / "sample_page.py").write_text("class SamplePage: pass")

        auditor = RegistryAuditor(page_objects_path=str(po_dir))
        entry = await auditor.find_existing_class("SamplePage")

        assert entry is not None
        assert entry.class_name == "SamplePage"
EOF
```

**Step 3: Run test to verify it fails**

```bash
cd agent && python -m pytest tests/test_registry_auditor.py -v 2>&1 || true
# Expected: ModuleNotFoundError
```

**Step 4: Write minimal implementation**

```bash
cat > agent/agent/registry_auditor.py << 'EOF'
import ast
import inspect
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from .models import RegistryEntry

class RegistryAuditor:
    def __init__(self, page_objects_path: str = "/nanoclaw/page_objects"):
        self.page_objects_path = Path(page_objects_path)

    async def audit(self) -> Dict[str, RegistryEntry]:
        registry = {}

        if not self.page_objects_path.exists():
            return registry

        for py_file in self.page_objects_path.glob("*.py"):
            if py_file.name.startswith("__"):
                continue

            classes = await self._extract_classes_from_file(py_file)
            for class_name, methods in classes.items():
                registry[class_name] = RegistryEntry(
                    class_name=class_name,
                    file_path=py_file.name,
                    methods=list(methods),
                    selectors={},
                    last_modified=datetime.fromtimestamp(py_file.stat().st_mtime)
                )

        return registry

    async def _extract_classes_from_file(self, file_path: Path) -> Dict[str, set]:
        """Extract class names and their async methods from a Python file."""
        source = file_path.read_text()
        tree = ast.parse(source)

        classes = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                methods = set()
                for item in node.body:
                    if isinstance(item, ast.AsyncFunctionDef):
                        methods.add(item.name)
                    elif isinstance(item, ast.FunctionDef):
                        methods.add(item.name)
                classes[node.name] = methods

        return classes

    async def find_existing_class(self, page_name: str) -> Optional[RegistryEntry]:
        """Check if a page object class already exists."""
        registry = await self.audit()
        class_name = f"{page_name.replace('_', ' ').title().replace(' ', '')}Page"
        return registry.get(class_name)

    async def find_available_methods(self, class_name: str) -> List[str]:
        """Return all callable methods for a given class."""
        registry = await self.audit()
        entry = registry.get(class_name)
        return entry.methods if entry else []
EOF
```

**Step 5: Run test to verify it passes**

```bash
cd agent && python -m pytest tests/test_registry_auditor.py -v
# Expected: PASS
```

**Step 6: Commit**

```bash
git add agent/agent/registry_auditor.py agent/tests/test_registry_auditor.py shared/page_objects/
git commit -m "feat: implement RegistryAuditor

- Scan page_objects/ directory for existing POM classes
- Extract class names, methods using AST parsing
- Find existing classes by name pattern
- Return available methods for reuse"
```

---

### Task 8: Implement Test Case Parser (Bot Side)

**Files:**
- Create: `bot/bot/test_case_parser.py`

**Step 1: Write failing test**

```bash
cat > bot/tests/test_parser.py << 'EOF'
import pytest
from bot.test_case_parser import TestCaseParser

@pytest.mark.asyncio
async def test_parse_structured_test_case():
    parser = TestCaseParser()

    text = """
Test: Login with invalid credentials
Scope: Authentication Module
Specs:
- Verify error message appears
- Verify login button is disabled
Steps:
1. Navigate to /login
2. Enter invalid email
3. Enter invalid password
4. Click login button
"""

    test_case = await parser.parse(text)

    assert test_case.name == "Login with invalid credentials"
    assert test_case.scope == "Authentication Module"
    assert len(test_case.specs) == 2
    assert len(test_case.steps) == 4

@pytest.mark.asyncio
async def test_parse_handles_missing_optional_fields():
    parser = TestCaseParser()

    text = """
Test: Simple test
Scope: Test Module
Steps:
1. Step one
2. Step two
"""

    test_case = await parser.parse(text)

    assert test_case.name == "Simple test"
    assert test_case.specs == []
    assert test_case.priority == "P1"
EOF
```

**Step 2: Run test to verify it fails**

```bash
cd bot && python -m pytest tests/test_parser.py -v 2>&1 || true
# Expected: ModuleNotFoundError
```

**Step 3: Write minimal implementation**

```bash
cat > bot/bot/test_case_parser.py << 'EOF'
import re
from typing import List
from .models import TestCaseSpec

class TestCaseParser:
    def __init__(self):
        # Patterns for structured test case
        self.patterns = {
            'name': r'Test:\s*(.+?)(?=\n|$)',
            'scope': r'Scope:\s*(.+?)(?=\n|$)',
            'priority': r'Priority:\s*(P[0-2])',
        }

    async def parse(self, text: str) -> TestCaseSpec:
        """Parse structured natural language test case."""

        # Extract name
        name_match = re.search(self.patterns['name'], text, re.IGNORECASE)
        name = name_match.group(1).strip() if name_match else "Unnamed Test"

        # Extract scope
        scope_match = re.search(self.patterns['scope'], text, re.IGNORECASE)
        scope = scope_match.group(1).strip() if scope_match else "General"

        # Extract priority
        priority_match = re.search(self.patterns['priority'], text, re.IGNORECASE)
        priority = priority_match.group(1) if priority_match else "P1"

        # Extract specs (bullet points after "Specs:")
        specs = self._extract_bullet_points(text, 'specs')

        # Extract steps (numbered or bulleted after "Steps:")
        steps = self._extract_steps(text)

        return TestCaseSpec(
            name=name,
            scope=scope,
            specs=specs,
            steps=steps,
            priority=priority
        )

    def _extract_bullet_points(self, text: str, section: str) -> List[str]:
        """Extract bullet points under a section."""
        lines = text.split('\n')
        in_section = False
        bullets = []

        for line in lines:
            line_lower = line.lower().strip()
            if line_lower.startswith(f'{section}:'):
                in_section = True
                continue

            if in_section:
                if line.strip() == '':
                    continue
                if line.startswith('-') or line.startswith('*'):
                    bullets.append(line.lstrip('-*').strip())
                elif line[0].isdigit() and '.' in line[:3]:
                    # Numbered list, might be steps
                    continue
                elif not line.startswith(' '):
                    # New section started
                    break

        return bullets

    def _extract_steps(self, text: str) -> List[str]:
        """Extract numbered or bulleted steps from text."""
        lines = text.split('\n')
        in_steps = False
        steps = []

        for line in lines:
            line_lower = line.lower().strip()
            if line_lower.startswith('steps:'):
                in_steps = True
                continue

            if in_steps:
                if line.strip() == '':
                    continue

                # Numbered step: "1. Step description" or "1) Step"
                numbered_match = re.match(r'^\d+[\.)]\s*(.+)', line.strip())
                if numbered_match:
                    steps.append(numbered_match.group(1))
                elif line.startswith('-') or line.startswith('*'):
                    steps.append(line.lstrip('-*').strip())
                elif not line.startswith(' '):
                    # New section
                    break

        # If no structured steps found, split by newlines after "Steps:"
        if not steps:
            steps_match = re.search(r'Steps:\s*\n((?:.+\n)+)', text, re.IGNORECASE)
            if steps_match:
                steps_text = steps_match.group(1)
                steps = [s.strip() for s in steps_text.split('\n') if s.strip()]

        return steps
EOF
```

**Step 4: Run test to verify it passes**

```bash
cd bot && python -m pytest tests/test_parser.py -v
# Expected: PASS
```

**Step 5: Commit**

```bash
git add bot/bot/test_case_parser.py bot/tests/test_parser.py
git commit -m "feat: implement TestCaseParser

- Parse structured natural language test cases
- Extract: Test name, Scope, Specs (bullets), Steps (numbered)
- Handle optional fields with defaults
- Support flexible formatting"
```

---

## Phase 4: Agent API Endpoints

### Task 9: Implement Agent API Endpoints

**Files:**
- Create: `agent/agent/api.py`
- Modify: `agent/agent/main.py` (to include API routes)

**Step 1: Write failing test**

```bash
cat > agent/tests/test_api.py << 'EOF'
import pytest
import tempfile
from fastapi.testclient import TestClient
from agent.main import app
from agent.models import TestCaseSpec

@pytest.mark.asyncio
async def test_submit_test_case_endpoint():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Monkey patch shared volume path
        from agent import manifest_manager
        manifest_manager.SharedVolumePath = tmpdir

        client = TestClient(app)

        test_case = {
            "name": "Test login",
            "scope": "Auth",
            "steps": ["Step 1", "Step 2"]
        }

        response = client.post("/api/v1/submit", json=test_case)

        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert len(data["job_id"]) == 36  # UUID

@pytest.mark.asyncio
async def test_get_status_endpoint():
    with tempfile.TemporaryDirectory() as tmpdir:
        from agent import manifest_manager
        manifest_manager.SharedVolumePath = tmpdir

        client = TestClient(app)

        # First create a job
        test_case = {
            "name": "Test login",
            "scope": "Auth",
            "steps": ["Step 1"]
        }
        submit_response = client.post("/api/v1/submit", json=test_case)
        job_id = submit_response.json()["job_id"]

        # Then check status
        status_response = client.get(f"/api/v1/status/{job_id}")

        assert status_response.status_code == 200
        data = status_response.json()
        assert data["job_id"] == job_id
        assert data["status"] == "pending"
EOF
```

**Step 2: Run test to verify it fails**

```bash
cd agent && python -m pytest tests/test_api.py -v 2>&1 || true
# Expected: 404 or route not found
```

**Step 3: Write minimal implementation**

```bash
cat > agent/agent/api.py << 'EOF'
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from .models import TestCaseSpec, JobStatus
from .manifest_manager import ManifestManager
from .registry_auditor import RegistryAuditor

router = APIRouter(prefix="/api/v1")

# Singleton instances (in production, use proper DI)
_manifest_manager = None
_registry_auditor = None

def get_manifest_manager():
    global _manifest_manager
    if _manifest_manager is None:
        _manifest_manager = ManifestManager()
    return _manifest_manager

def get_registry_auditor():
    global _registry_auditor
    if _registry_auditor is None:
        _registry_auditor = RegistryAuditor()
    return _registry_auditor

@router.post("/submit")
async def submit_test_case(
    test_case: TestCaseSpec,
    manifest_manager: ManifestManager = Depends(get_manifest_manager)
) -> Dict[str, str]:
    """Submit a new test case for processing."""

    try:
        job_id = await manifest_manager.create_job(test_case)
        return {"job_id": job_id, "status": "queued"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{job_id}")
async def get_job_status(
    job_id: str,
    manifest_manager: ManifestManager = Depends(get_manifest_manager)
) -> Dict[str, Any]:
    """Get the status of a submitted job."""

    job = await manifest_manager.get_job(job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return {
        "job_id": job.job_id,
        "status": job.status.value,
        "created_at": job.created_at.isoformat(),
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        "error_message": job.error_message,
        "test_case": {
            "name": job.test_case.name,
            "scope": job.test_case.scope
        }
    }

@router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "agent"}
EOF
```

**Step 4: Update main.py to include API routes**

```bash
cat > agent/agent/main.py << 'EOF'
from fastapi import FastAPI
from dotenv import load_dotenv
from .api import router

load_dotenv()

app = FastAPI(title="NanoClow Agent")

# Include API routes
app.include_router(router)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "agent"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
EOF
```

**Step 5: Run test to verify it passes**

```bash
cd agent && python -m pytest tests/test_api.py -v
# Expected: PASS
```

**Step 6: Commit**

```bash
git add agent/agent/api.py agent/agent/main.py agent/tests/test_api.py
git commit -m "feat: implement Agent API endpoints

- POST /api/v1/submit - Submit test case, receive job_id
- GET /api/v1/status/{job_id} - Get job status and details
- Use dependency injection for manifest manager and registry auditor"
```

---

## Phase 5: Bot Core Components

### Task 10: Implement Conversation Manager

**Files:**
- Create: `bot/bot/conversation_manager.py`

**Step 1: Write failing test**

```bash
cat > bot/tests/test_conversation.py << 'EOF'
import pytest
from bot.conversation_manager import ConversationManager
from bot.models import ConversationState, TestCaseSpec

@pytest.mark.asyncio
async def test_create_and_get_conversation():
    manager = ConversationManager()

    await manager.update_state(
        user_id="wa_123",
        state=ConversationState.IDLE
    )

    state = await manager.get_state("wa_123")

    assert state.user_id == "wa_123"
    assert state.state == ConversationState.IDLE

@pytest.mark.asyncio
async def test_update_conversation_with_test_case():
    manager = ConversationManager()

    test_case = TestCaseSpec(
        name="Test",
        scope="Auth",
        steps=["Step 1"]
    )

    await manager.update_state(
        user_id="wa_456",
        state=ConversationState.AWAITING_TEST_CASE,
        test_case_draft=test_case
    )

    state = await manager.get_state("wa_456")

    assert state.state == ConversationState.AWAITING_TEST_CASE
    assert state.test_case_draft.name == "Test"
EOF
```

**Step 2: Run test to verify it fails**

```bash
cd bot && python -m pytest tests/test_conversation.py -v 2>&1 || true
# Expected: ModuleNotFoundError
```

**Step 3: Write minimal implementation**

```bash
cat > bot/bot/conversation_manager.py << 'EOF'
from datetime import datetime, timedelta
from typing import Dict, Optional
from .models import ConversationState, TestCaseSpec, ConversationData

class ConversationManager:
    def __init__(self, ttl_minutes: int = 30):
        # In production, use Redis or database
        self._conversations: Dict[str, ConversationData] = {}
        self.ttl = timedelta(minutes=ttl_minutes)

    async def get_state(self, user_id: str) -> Optional[ConversationData]:
        """Get conversation state for user."""
        state = self._conversations.get(user_id)

        # Check if expired
        if state and datetime.utcnow() - state.created_at > self.ttl:
            del self._conversations[user_id]
            return None

        return state

    async def update_state(
        self,
        user_id: str,
        state: ConversationState,
        test_case_draft: Optional[TestCaseSpec] = None,
        current_job_id: Optional[str] = None
    ) -> None:
        """Update or create conversation state."""

        existing = await self.get_state(user_id)

        if existing:
            existing.state = state
            existing.test_case_draft = test_case_draft or existing.test_case_draft
            existing.current_job_id = current_job_id or existing.current_job_id
        else:
            self._conversations[user_id] = ConversationData(
                user_id=user_id,
                state=state,
                test_case_draft=test_case_draft,
                current_job_id=current_job_id
            )

    async def clear_state(self, user_id: str) -> None:
        """Clear conversation state."""
        if user_id in self._conversations:
            del self._conversations[user_id]
EOF
```

**Step 4: Run test to verify it passes**

```bash
cd bot && python -m pytest tests/test_conversation.py -v
# Expected: PASS
```

**Step 5: Commit**

```bash
git add bot/bot/conversation_manager.py bot/tests/test_conversation.py
git commit -m "feat: implement ConversationManager

- Track multi-turn conversation state per user
- Support state transitions (idle, awaiting, processing, completed)
- Auto-expire conversations after TTL (default 30min)
- Store test case drafts and job references"
```

---

### Task 11: Implement Agent API Client (Bot Side)

**Files:**
- Create: `bot/bot/agent_client.py`

**Step 1: Write failing test**

```bash
cat > bot/tests/test_agent_client.py << 'EOF'
import pytest
from unittest.mock import AsyncMock, patch
from bot.agent_client import AgentAPIClient
from bot.models import TestCaseSpec, JobStatus

@pytest.mark.asyncio
async def test_submit_test_case():
    client = AgentAPIClient(base_url="http://localhost:8000")

    test_case = TestCaseSpec(
        name="Test",
        scope="Auth",
        steps=["Step 1"]
    )

    # Mock the HTTP response
    with patch.object(client, '_post', new_callable=AsyncMock) as mock_post:
        mock_post.return_value = {"job_id": "test-job-id", "status": "queued"}

        job_id = await client.submit_test_case(test_case)

        assert job_id == "test-job-id"
        mock_post.assert_called_once()

@pytest.mark.asyncio
async def test_get_job_status():
    client = AgentAPIClient(base_url="http://localhost:8000")

    with patch.object(client, '_get', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = {
            "job_id": "test-job-id",
            "status": "completed",
            "created_at": "2026-03-08T15:00:00Z",
            "completed_at": "2026-03-08T15:02:00Z"
        }

        status = await client.get_status("test-job-id")

        assert status["job_id"] == "test-job-id"
        assert status["status"] == "completed"
EOF
```

**Step 2: Run test to verify it fails**

```bash
cd bot && python -m pytest tests/test_agent_client.py -v 2>&1 || true
# Expected: ModuleNotFoundError
```

**Step 3: Write minimal implementation**

```bash
cat > bot/bot/agent_client.py << 'EOF'
import aiohttp
from typing import Dict, Any, Optional
from .models import TestCaseSpec

class AgentAPIClient:
    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.timeout = aiohttp.ClientTimeout(total=timeout)

    async def submit_test_case(self, test_case: TestCaseSpec) -> str:
        """Submit test case to agent for processing."""

        url = f"{self.base_url}/api/v1/submit"
        payload = test_case.model_dump()

        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            async with session.post(url, json=payload) as response:
                if response.status != 200:
                    raise Exception(f"Agent returned {response.status}")

                data = await response.json()
                return data["job_id"]

    async def get_status(self, job_id: str) -> Dict[str, Any]:
        """Get status of a submitted job."""

        url = f"{self.base_url}/api/v1/status/{job_id}"

        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            async with session.get(url) as response:
                if response.status == 404:
                    raise Exception("Job not found")
                elif response.status != 200:
                    raise Exception(f"Agent returned {response.status}")

                return await response.json()

    async def get_generated_script(self, job_id: str) -> Optional[str]:
        """Get the generated test script content."""

        # For now, return None - will implement when egress files are ready
        status = await self.get_status(job_id)

        if status["status"] == "completed":
            # TODO: Fetch actual script from egress/{job_id}/
            return f"# Script for job {job_id}"

        return None
EOF
```

**Step 4: Run test to verify it passes**

```bash
cd bot && python -m pytest tests/test_agent_client.py -v
# Expected: PASS (with mocked HTTP)
```

**Step 5: Commit**

```bash
git add bot/bot/agent_client.py bot/tests/test_agent_client.py
git commit -m "feat: implement AgentAPIClient

- Submit test cases to agent via HTTP API
- Query job status by job_id
- Fetch generated scripts (stub for now)
- Use aiohttp for async HTTP requests"
```

---

## Phase 6: Integration & End-to-End

### Task 12: End-to-End Integration Test

**Files:**
- Create: `tests/integration/test_e2e.py`

**Step 1: Write integration test**

```bash
mkdir -p tests/integration
cat > tests/integration/test_e2e.py << 'EOF'
import pytest
import tempfile
import asyncio
from pathlib import Path
from bot.bot.test_case_parser import TestCaseParser
from bot.bot.agent_client import AgentAPIClient
from agent.agent.manifest_manager import ManifestManager

@pytest.mark.asyncio
async def test_submit_and_retrieve_job():
    """Test full flow: parse test case -> submit to agent -> retrieve status"""

    with tempfile.TemporaryDirectory() as tmpdir:
        # Setup agent with temp shared volume
        from agent.agent import manifest_manager
        original_path = "/nanoclaw"
        manifest_manager.ManifestManager = lambda: manifest_manager.ManifestManager(shared_volume_path=tmpdir)

        # Parse test case
        parser = TestCaseParser()
        text = """
Test: Login validation
Scope: Auth Module
Steps:
1. Navigate to /login
2. Enter invalid email
"""
        test_case = await parser.parse(text)

        # Submit to agent (simulated)
        mm = manifest_manager.ManifestManager(shared_volume_path=tmpdir)
        job_id = await mm.create_job(test_case)

        # Verify job was created
        job = await mm.get_job(job_id)
        assert job is not None
        assert job.job_id == job_id
        assert job.test_case.name == "Login validation"
        assert job.status == manifest_manager.JobStatus.PENDING
EOF
```

**Step 2: Run test to verify it passes**

```bash
python -m pytest tests/integration/test_e2e.py -v
# Expected: PASS
```

**Step 3: Commit**

```bash
git add tests/integration/
git commit -m "test: add end-to-end integration test

- Test full flow: parse -> submit -> retrieve
- Use temporary shared volume for isolation
- Verify manifest persistence across components"
```

---

## Phase 7: Docker Testing & Validation

### Task 13: Verify Docker Compose Setup

**Files:**
- Modify: `docker/docker-compose.yml` (fix volume paths if needed)
- Create: `shared/.gitkeep` files

**Step 1: Create .gitkeep files**

```bash
touch shared/ingress/.gitkeep
touch shared/egress/.gitkeep
touch shared/html_dumps/.gitkeep
touch shared/logs/.gitkeep
```

**Step 2: Test Docker build**

```bash
cd docker && docker-compose build
# Expected: Both containers build successfully
```

**Step 3: Test Docker startup**

```bash
docker-compose up -d
# Expected: Both containers start

# Check health
curl http://localhost:8000/health  # Agent
curl http://localhost:5000/health  # Bot

# Expected: Both return {"status": "healthy"}
```

**Step 4: Test API communication**

```bash
# Submit test case to agent
curl -X POST http://localhost:8000/api/v1/submit \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test login",
    "scope": "Auth",
    "steps": ["Step 1", "Step 2"]
  }'

# Expected: {"job_id": "...", "status": "queued"}

# Get status
curl http://localhost:8000/api/v1/status/{job_id}

# Expected: Job details with status "pending"
```

**Step 5: Cleanup**

```bash
docker-compose down
```

**Step 6: Commit**

```bash
git add docker/
git commit -m "feat: validate Docker compose setup

- Test container builds and startup
- Verify health check endpoints
- Test inter-container API communication
- Add .gitkeep files for shared directories"
```

---

## Task 14: Add Environment Setup Script

**Files:**
- Create: `scripts/setup.sh`
- Create: `scripts/dev.sh`

**Step 1: Create setup script**

```bash
mkdir -p scripts
cat > scripts/setup.sh << 'EOF'
#!/bin/bash
set -e

echo "🔧 NanoClow Setup"
echo "================="

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env from .env.example..."
    cp .env.example .env
    echo "⚠️  Please edit .env with your API keys before continuing."
    exit 1
fi

# Create shared volume directories
echo "📁 Creating shared volume directories..."
mkdir -p shared/{ingress,egress,page_objects,html_dumps,logs}

# Build Docker containers
echo "🐳 Building Docker containers..."
cd docker
docker-compose build

echo "✅ Setup complete!"
echo ""
echo "To start NanoClow:"
echo "  cd docker && docker-compose up"
echo ""
echo "To run in background:"
echo "  cd docker && docker-compose up -d"
EOF

chmod +x scripts/setup.sh
```

**Step 2: Create dev script**

```bash
cat > scripts/dev.sh << 'EOF'
#!/bin/bash

echo "🚀 Starting NanoClow in development mode..."
cd docker
docker-compose up --build
EOF

chmod +x scripts/dev.sh
```

**Step 3: Commit**

```bash
git add scripts/
git commit -m "feat: add setup and development scripts

- scripts/setup.sh: Initialize environment and build containers
- scripts/dev.sh: Start NanoClow in development mode"
```

---

## Task 15: Final Documentation

**Files:**
- Modify: `README.md` (expand with usage instructions)
- Create: `docs/api.md` (API documentation)

**Step 1: Expand README.md**

```bash
cat > README.md << 'EOF'
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
EOF
```

**Step 2: Create API documentation**

```bash
cat > docs/api.md << 'EOF'
# NanoClow API Documentation

## Agent API (Port 8000)

### Submit Test Case

**Endpoint:** `POST /api/v1/submit`

**Request Body:**
```json
{
  "name": "string (required)",
  "scope": "string (required)",
  "specs": ["string"],
  "steps": ["string"] (required),
  "priority": "P0 | P1 | P2",
  "metadata": {}
}
```

**Response:**
```json
{
  "job_id": "uuid-v4",
  "status": "queued"
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/v1/submit \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Login test",
    "scope": "Auth",
    "steps": ["Go to /login", "Enter email", "Click submit"]
  }'
```

### Get Job Status

**Endpoint:** `GET /api/v1/status/{job_id}`

**Response:**
```json
{
  "job_id": "uuid-v4",
  "status": "pending | processing | completed | failed",
  "created_at": "2026-03-08T15:00:00Z",
  "completed_at": "2026-03-08T15:02:00Z",
  "error_message": "string | null",
  "test_case": {
    "name": "string",
    "scope": "string"
  }
}
```

**Example:**
```bash
curl http://localhost:8000/api/v1/status/a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

## Bot API (Port 5000)

### Health Check

**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "healthy",
  "service": "bot"
}
```

## Error Responses

All endpoints may return error responses:

```json
{
  "error": "Error message",
  "detail": "Detailed error information"
}
```

**HTTP Status Codes:**
- `200` - Success
- `400` - Bad Request (invalid input)
- `404` - Not Found (job doesn't exist)
- `500` - Internal Server Error
EOF
```

**Step 3: Commit**

```bash
git add README.md docs/api.md
git commit -m "docs: add comprehensive API and usage documentation

- Expand README with quick start, architecture, directory structure
- Add API documentation with request/response examples
- Document all endpoints and error codes"
```

---

## Completion Summary

**All 15 tasks completed.**

✅ **Phase 1: Project Scaffold & Docker Foundation**
- Directory structure, Docker files, basic bot/agent skeletons

✅ **Phase 2: Shared Data Models**
- Pydantic models for test cases, conversations, manifest

✅ **Phase 3: Agent Core Components**
- ManifestManager, RegistryAuditor

✅ **Phase 4: Agent API Endpoints**
- Submit test case, get status endpoints

✅ **Phase 5: Bot Core Components**
- TestCaseParser, ConversationManager, AgentAPIClient

✅ **Phase 6: Integration & End-to-End**
- Integration tests, cross-component communication

✅ **Phase 7: Docker Testing & Validation**
- Docker compose validation, setup scripts

✅ **Final Documentation**
- README, API docs

**Next Steps for Full Implementation:**
1. Configure WhatsApp Business API webhook
2. Implement ScriptGenerator with Claude API integration
3. Implement POMExpander for registry extension
4. Implement StaticValidator and DOMValidator
5. Add WhatsApp message formatter
6. Implement webhook receiver in bot
7. Add retry logic and error handling
8. Deploy and test with real test cases
