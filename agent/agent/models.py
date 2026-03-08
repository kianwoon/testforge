from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict, Any
from datetime import datetime, timezone
from enum import Enum


def utcnow() -> datetime:
    """Return current UTC time as timezone-aware datetime (Python 3.12+ compatible)."""
    return datetime.now(tz=timezone.utc)


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
    created_at: datetime = Field(default_factory=utcnow)
    processing_at: Optional[datetime] = None  # When job started processing
    completed_at: Optional[datetime] = None   # When job finished (success or failure)


class Manifest(BaseModel):
    version: str = "1.0.0"
    last_updated: datetime = Field(default_factory=utcnow)
    statistics: Dict[str, int] = Field(
        default_factory=lambda: {"total_jobs": 0, "completed": 0, "failed": 0, "pending": 0, "processing": 0}
    )
    jobs: List[ManifestEntry] = Field(default_factory=list)
