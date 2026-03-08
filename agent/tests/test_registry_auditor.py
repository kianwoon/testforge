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
