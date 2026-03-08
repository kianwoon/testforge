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
            specs=["Spec 1"],
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
            specs=["Spec 1"],
            steps=["Step 1"]
        )

        job_id = await manager.create_job(test_case)
        await manager.update_job_status(job_id, JobStatus.COMPLETED)

        job = await manager.get_job(job_id)
        assert job.status == JobStatus.COMPLETED
        assert job.completed_at is not None


@pytest.mark.asyncio
async def test_get_job_returns_none_for_nonexistent():
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = ManifestManager(shared_volume_path=tmpdir)

        job = await manager.get_job("nonexistent-id")
        assert job is None


@pytest.mark.asyncio
async def test_statistics_update_on_job_creation():
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = ManifestManager(shared_volume_path=tmpdir)

        test_case = TestCaseSpec(
            name="Test login",
            scope="Auth",
            specs=["Spec 1"],
            steps=["Step 1"]
        )

        await manager.create_job(test_case)
        await manager.create_job(test_case)

        manifest = await manager._load_manifest()
        assert manifest.statistics["total_jobs"] == 2
        assert manifest.statistics["pending"] == 2


@pytest.mark.asyncio
async def test_statistics_update_on_completion():
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = ManifestManager(shared_volume_path=tmpdir)

        test_case = TestCaseSpec(
            name="Test login",
            scope="Auth",
            specs=["Spec 1"],
            steps=["Step 1"]
        )

        job_id = await manager.create_job(test_case)
        await manager.update_job_status(job_id, JobStatus.COMPLETED)

        manifest = await manager._load_manifest()
        assert manifest.statistics["completed"] == 1
        assert manifest.statistics["pending"] == 0


@pytest.mark.asyncio
async def test_statistics_update_on_failure():
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = ManifestManager(shared_volume_path=tmpdir)

        test_case = TestCaseSpec(
            name="Test login",
            scope="Auth",
            specs=["Spec 1"],
            steps=["Step 1"]
        )

        job_id = await manager.create_job(test_case)
        await manager.update_job_status(job_id, JobStatus.FAILED, error_message="Test failed")

        manifest = await manager._load_manifest()
        assert manifest.statistics["failed"] == 1
        assert manifest.statistics["pending"] == 0


@pytest.mark.asyncio
async def test_atomic_write_with_temp_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = ManifestManager(shared_volume_path=tmpdir)

        test_case = TestCaseSpec(
            name="Test login",
            scope="Auth",
            specs=["Spec 1"],
            steps=["Step 1"]
        )

        await manager.create_job(test_case)

        # Check that temp file was cleaned up
        temp_files = list(Path(tmpdir).glob("*.tmp"))
        assert len(temp_files) == 0

        # Check that manifest.json exists
        manifest_path = Path(tmpdir) / "manifest.json"
        assert manifest_path.exists()


@pytest.mark.asyncio
async def test_statistics_update_on_processing():
    """Test PENDING -> PROCESSING transition updates counters correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = ManifestManager(shared_volume_path=tmpdir)

        test_case = TestCaseSpec(
            name="Test login",
            scope="Auth",
            specs=["Spec 1"],
            steps=["Step 1"]
        )

        job_id = await manager.create_job(test_case)
        await manager.update_job_status(job_id, JobStatus.PROCESSING)

        manifest = await manager._load_manifest()
        assert manifest.statistics["pending"] == 0
        assert manifest.statistics["processing"] == 1


@pytest.mark.asyncio
async def test_processing_to_completed():
    """Test PROCESSING -> COMPLETED transition updates counters correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = ManifestManager(shared_volume_path=tmpdir)

        test_case = TestCaseSpec(
            name="Test login",
            scope="Auth",
            specs=["Spec 1"],
            steps=["Step 1"]
        )

        job_id = await manager.create_job(test_case)
        await manager.update_job_status(job_id, JobStatus.PROCESSING)
        await manager.update_job_status(job_id, JobStatus.COMPLETED)

        manifest = await manager._load_manifest()
        assert manifest.statistics["processing"] == 0
        assert manifest.statistics["completed"] == 1
        assert manifest.statistics["pending"] == 0


@pytest.mark.asyncio
async def test_update_nonexistent_job_raises_error():
    """Test that updating a non-existent job raises ValueError."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = ManifestManager(shared_volume_path=tmpdir)

        with pytest.raises(ValueError, match="Job nonexistent-id not found"):
            await manager.update_job_status("nonexistent-id", JobStatus.COMPLETED)
