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
