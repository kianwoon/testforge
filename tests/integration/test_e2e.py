# tests/integration/test_e2e.py
import pytest
import tempfile
from pathlib import Path
from bot.bot.test_case_parser import TestCaseParser
from bot.bot.agent_client import AgentAPIClient
from agent.agent.manifest_manager import ManifestManager
from agent.agent.models import TestCaseSpec, JobStatus

@pytest.mark.asyncio
async def test_submit_and_retrieve_job():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Parse test case using bot's parser
        parser = TestCaseParser()
        text = """
Test: Login validation
Scope: Auth Module
Steps:
1. Navigate to /login
2. Enter invalid email
"""
        bot_test_case = await parser.parse(text)

        # Convert to agent's TestCaseSpec model
        test_case = TestCaseSpec(
            name=bot_test_case.name,
            scope=bot_test_case.scope,
            specs=bot_test_case.specs,
            steps=bot_test_case.steps,
            priority=bot_test_case.priority,
            metadata=bot_test_case.metadata
        )

        # Submit to agent (simulated with temp shared volume)
        mm = ManifestManager(shared_volume_path=tmpdir)
        job_id = await mm.create_job(test_case)

        # Verify job was created
        job = await mm.get_job(job_id)
        assert job is not None
        assert job.job_id == job_id
        assert job.test_case.name == "Login validation"
        assert job.status == JobStatus.PENDING
