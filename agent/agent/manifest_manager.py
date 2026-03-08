import asyncio
import json
import uuid
from pathlib import Path
from datetime import datetime
from typing import Optional
import aiofiles
from .models import ManifestEntry, Manifest, TestCaseSpec, JobStatus


class ManifestManager:
    """
    Manages the atomic manifest.json operations - the source of truth for job state.
    """

    def __init__(self, shared_volume_path: str = "/nanoclaw"):
        self.shared_volume = Path(shared_volume_path)
        self.manifest_path = self.shared_volume / "manifest.json"
        self._lock = asyncio.Lock()

    async def _load_manifest(self) -> Manifest:
        """Load manifest from disk, or create new if doesn't exist."""
        if not self.manifest_path.exists():
            return Manifest()

        async with aiofiles.open(self.manifest_path, 'r') as f:
            data = json.loads(await f.read())
            return Manifest(**data)

    async def _save_manifest(self, manifest: Manifest) -> None:
        """
        Save manifest to disk using atomic write pattern.
        Uses temp file + rename to prevent corruption.
        """
        # Ensure directory exists
        self.shared_volume.mkdir(parents=True, exist_ok=True)

        # Atomic write: temp file + rename
        temp_path = self.manifest_path.with_suffix('.tmp')
        manifest.last_updated = datetime.utcnow()

        async with aiofiles.open(temp_path, 'w') as f:
            await f.write(manifest.model_dump_json(indent=2))

        # Atomic rename
        temp_path.rename(self.manifest_path)

    async def create_job(self, test_case: TestCaseSpec) -> str:
        """
        Create a new job entry in the manifest.
        Returns the unique job ID (UUID4).
        """
        async with self._lock:
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
        """
        Update job status and optional fields.
        Handles statistics tracking automatically.
        """
        async with self._lock:
            manifest = await self._load_manifest()

            for job in manifest.jobs:
                if job.job_id == job_id:
                    old_status = job.status
                    job.status = status

                    # Decrement whichever counter the job is leaving
                    if old_status == JobStatus.PENDING:
                        manifest.statistics["pending"] = max(0, manifest.statistics["pending"] - 1)
                    elif old_status == JobStatus.PROCESSING:
                        manifest.statistics["processing"] = max(0, manifest.statistics["processing"] - 1)

                    # Increment counter for new status
                    if status == JobStatus.PROCESSING:
                        manifest.statistics["processing"] += 1
                    elif status == JobStatus.COMPLETED:
                        job.completed_at = datetime.utcnow()
                        manifest.statistics["completed"] += 1
                    elif status == JobStatus.FAILED:
                        manifest.statistics["failed"] += 1

                    # Update any additional fields passed via kwargs
                    for key, value in kwargs.items():
                        setattr(job, key, value)

                    break

            await self._save_manifest(manifest)

    async def get_job(self, job_id: str) -> Optional[ManifestEntry]:
        """
        Retrieve a job by ID.
        Returns None if job not found.
        """
        manifest = await self._load_manifest()

        for job in manifest.jobs:
            if job.job_id == job_id:
                return job

        return None
