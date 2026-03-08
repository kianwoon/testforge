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
        self._lock: Optional[asyncio.Lock] = None  # Lazy init

    def _get_lock(self) -> asyncio.Lock:
        """Get or create lock lazily (requires running event loop)."""
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock

    def _update_statistics(
        self,
        statistics: dict,
        old_status: JobStatus,
        new_status: JobStatus
    ) -> None:
        """Update statistics counters for status transitions."""
        status_to_counter = {
            JobStatus.PENDING: "pending",
            JobStatus.PROCESSING: "processing",
            JobStatus.COMPLETED: "completed",
            JobStatus.FAILED: "failed",
        }

        # Decrement old status counter
        if old_status in status_to_counter:
            counter = status_to_counter[old_status]
            statistics[counter] = max(0, statistics.get(counter, 0) - 1)

        # Increment new status counter
        if new_status in status_to_counter:
            counter = status_to_counter[new_status]
            statistics[counter] = statistics.get(counter, 0) + 1

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
        async with self._get_lock():
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

        Raises:
            ValueError: If job_id is not found in manifest
        """
        async with self._get_lock():
            manifest = await self._load_manifest()

            job_found = False
            for job in manifest.jobs:
                if job.job_id == job_id:
                    old_status = job.status
                    job.status = status

                    # Update statistics counters
                    self._update_statistics(manifest.statistics, old_status, status)

                    # Set completed_at for completed jobs
                    if status == JobStatus.COMPLETED:
                        job.completed_at = datetime.utcnow()

                    # Update any additional fields passed via kwargs
                    for key, value in kwargs.items():
                        setattr(job, key, value)

                    job_found = True
                    break

            if not job_found:
                raise ValueError(f"Job {job_id} not found in manifest")

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
