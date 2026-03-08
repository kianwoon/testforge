import os
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, Optional
from .models import TestCaseSpec, JobStatus
from .manifest_manager import ManifestManager

router = APIRouter(prefix="/api/v1")

_manifest_manager = None

def get_manifest_manager(shared_volume_path: Optional[str] = None):
    global _manifest_manager
    if _manifest_manager is None:
        path = shared_volume_path or os.getenv("SHARED_VOLUME_PATH", "/tmp/nanoclaw")
        _manifest_manager = ManifestManager(shared_volume_path=path)
    return _manifest_manager

@router.post("/submit")
async def submit_test_case(
    test_case: TestCaseSpec,
    manifest_manager: ManifestManager = Depends(get_manifest_manager)
) -> Dict[str, str]:
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
