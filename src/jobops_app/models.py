from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, HttpUrl


class JobApplication(BaseModel):
    id: str
    canonical_url: str
    job_title: Optional[str] = None
    company_name: Optional[str] = None
    application_date: Optional[str] = None
    status: str = "draft"
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class SectionPayload(BaseModel):
    job_application_id: str
    section_name: str
    data: Dict[str, Any]
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
