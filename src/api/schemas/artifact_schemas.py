"""
Pydantic API Schemas for Phase 7 Artifact Management.
"""

from datetime import datetime

from pydantic import BaseModel, Field


class CreateArtifactRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=256)
    mime_type: str = "text/markdown"
    content_base64_or_text: str
    created_by_employee_id: str
    source_run_id: str | None = None
    task_id: str | None = None


class ArtifactResponse(BaseModel):
    id: str
    workspace_id: str
    name: str
    mime_type: str
    size_bytes: int
    checksum_sha256: str
    version: int
    created_by_employee_id: str
    status: str
    created_at: datetime
