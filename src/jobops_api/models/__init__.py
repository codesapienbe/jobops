from typing import Optional, List, Dict, Any
# Use the v1-compatible Field helper to avoid mixing v2 FieldInfo objects with v1 BaseModel,
# which caused SQLite binding errors (FieldInfo was being stored instead of actual values).
from pydantic.v1 import BaseModel, Field, root_validator
from pydantic import field_validator
from uuid import uuid4
from datetime import datetime
from enum import Enum

class PersonalInfo(BaseModel):
    name: Optional[str] = Field(None, description="Full name of the candidate")
    title: Optional[str] = Field(None, description="Professional title or current position")
    experience_years: Optional[str] = Field(None, description="Years of experience")
    location: Optional[str] = Field(None, description="Current location or address")
    email: Optional[str] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    linkedin: Optional[str] = Field(None, description="LinkedIn profile URL")
    website: Optional[str] = Field(None, description="Personal website or portfolio")
    github: Optional[str] = Field(None, description="GitHub profile URL")

class WorkExperience(BaseModel):
    position: Optional[str] = Field(None, description="Job title or position")
    company: Optional[str] = Field(None, description="Company or organization name")
    location: Optional[str] = Field(None, description="Work location")
    start_date: Optional[str] = Field(None, description="Start date of employment")
    end_date: Optional[str] = Field(None, description="End date or 'Present'")
    period: Optional[str] = Field(None, description="Duration period")
    description: Optional[str] = Field(None, description="Job description")
    responsibilities: Optional[List[str]] = Field(None, description="Key responsibilities and achievements")
    
    @validator('responsibilities', pre=True)
    def validate_responsibilities(cls, v):
        if isinstance(v, str):
            return [v] if v and v.lower() not in ['n/a', 'none', ''] else []
        return v or []

class Education(BaseModel):
    degree: Optional[str] = Field(None, description="Degree or qualification")
    institution: Optional[str] = Field(None, description="Educational institution")
    location: Optional[str] = Field(None, description="Institution location")
    start_date: Optional[str] = Field(None, description="Start date")
    end_date: Optional[str] = Field(None, description="End date or expected graduation")
    period: Optional[str] = Field(None, description="Duration period")
    gpa: Optional[str] = Field(None, description="GPA or grade")
    description: Optional[str] = Field(None, description="Additional details")
    coursework: Optional[List[str]] = Field(None, description="Relevant coursework")
    
    @validator('coursework', pre=True)
    def validate_coursework(cls, v):
        if isinstance(v, str):
            return [v] if v and v.lower() not in ['n/a', 'none', ''] else []
        return v or []

class Project(BaseModel):
    name: Optional[str] = Field(None, description="Project name")
    description: Optional[str] = Field(None, description="Project description")
    technologies: Optional[List[str]] = Field(None, description="Technologies used")
    url: Optional[str] = Field(None, description="Project URL or repository")
    start_date: Optional[str] = Field(None, description="Project start date")
    end_date: Optional[str] = Field(None, description="Project end date")

class Certification(BaseModel):
    name: Optional[str] = Field(None, description="Certification name")
    issuer: Optional[str] = Field(None, description="Issuing organization")
    date: Optional[str] = Field(None, description="Date obtained")
    expiry: Optional[str] = Field(None, description="Expiry date")
    credential_id: Optional[str] = Field(None, description="Credential ID")
    url: Optional[str] = Field(None, description="Verification URL")

class GenericDocument(BaseModel):
    content_type: Optional[str] = Field(None, description="Type of document content")
    title: Optional[str] = Field(None, description="Document title")
    author: Optional[str] = Field(None, description="Document author")
    date: Optional[str] = Field(None, description="Document date")
    organization: Optional[str] = Field(None, description="Related organization")
    key_points: List[str] = Field(default_factory=list, description="Main points or highlights")
    sections: Dict[str, Any] = Field(default_factory=dict, description="Document sections")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    @root_validator(pre=True)
    def handle_invalid_values(cls, values):
        for key, value in values.items():
            if isinstance(value, str) and value.lower() in {'n/a', 'none', '', 'null'}:
                values[key] = None
        return values

class JobData(BaseModel):
    """Structured job posting data for motivation letter generation."""
    model_config = {'arbitrary_types_allowed': True}
    id: Optional[str] = Field(default_factory=lambda: str(uuid4()))
    url: str
    title: str
    company: str
    description: str
    requirements: str
    location: Optional[str] = None
    salary: Optional[str] = None
    employment_type: Optional[str] = None
    seniority_level: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None
    benefits: Optional[str] = None
    technology_stack: Optional[str] = Field(None, description="Technologies used in the job")
    job_reference_number: Optional[str] = Field(None, description="Job reference or ID number")
    content_language: Optional[str] = Field(None, description="Detected language of the job posting content")
    company_offers: Optional[str] = Field(None, description="Related company offers (benefits, perks)")
    scraped_at: datetime = Field(default_factory=datetime.now)
    company_profile_url: Optional[str] = None
    company_profile: Optional[str] = None
    job_responsibilities: Optional[str] = None
    candidate_profile: Optional[str] = None

    @field_validator('url')
    @classmethod
    def validate_url(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')
        return v

class DocumentType(str, Enum):
    RESUME = "resume"
    COVER_LETTER = "cover_letter"
    JOB_DESCRIPTION = "job_description"
    REFERENCE_LETTER = "reference_letter"
    CERTIFICATION = "certification"
    OTHER = "other"

class Document(BaseModel):
    id: Optional[str] = Field(default_factory=lambda: str(uuid4()))
    type: DocumentType
    raw_content: str
    structured_content: str
    uploaded_at: datetime = Field(default_factory=datetime.now)
    group_id: Optional[str] = Field(None, description="Group identifier for related document sets")
    embedding: Optional[List[float]] = Field(None, description="Embedding vector for RAG usage")

class MotivationLetter(BaseModel):
    """Motivation letter generated for a specific job application."""
    model_config = {'arbitrary_types_allowed': True}
    id: Optional[str] = Field(default_factory=lambda: str(uuid4()))
    job_data: JobData
    resume: str  # Now just a markdown string
    content: str
    generated_at: datetime = Field(default_factory=datetime.now)

class AppConfig(BaseModel):
    backend: str = "ollama"
    backend_settings: Dict[str, Dict[str, Any]] = {
        'ollama': {'model': 'qwen3:8b', 'base_url': 'http://localhost:11434'},
        'openai': {'model': 'gpt-4o-mini', 'base_url': 'https://api.openai.com/v1'},
        'groq': {'model': 'llama-3.3-70b-versatile', 'base_url': 'https://api.groq.com/openai/v1'}
    }
    app_settings: Dict[str, Any] = {
        'language': 'en',
        'output_format': 'markdown'
    }
    sqlite_timeout: float = 30.0

# Add models for solicitation reporting
class Solicitation(BaseModel):
    id: Optional[str] = Field(default_factory=lambda: str(uuid4()), description="Unique ID for the solicitation record")
    report_id: Optional[str] = Field(None, description="ID of the solicitation report")
    datum: str
    bedrijf: str
    functie: str
    status: str
    resultaat: str
    locatie: str
    platform: str

class SolicitationReport(BaseModel):
    id: Optional[str] = Field(default_factory=lambda: str(uuid4()), description="Unique ID for the solicitation report")
    periode: str
    totaal_sollicitaties: int
    sollicitaties: List[Solicitation]
    status_overzicht: Dict[str, int]
    sollicitatie_platforms: List[str]
    locatie_verdeling: Dict[str, int]
    motivatiebrieven: Dict[str, int]
    interviews_assessments: Dict[str, Any]
    networking: Dict[str, Any]
    documenten_gereed: Dict[str, Any]
    vdab_opdrachten: Dict[str, Any]
    opmerkingen: str
    generated_at: datetime = Field(default_factory=datetime.now)

# ---------------------------------------------------------------------------
# Runtime-side helper models (UI ↔ workers ↔ services)
# ---------------------------------------------------------------------------


class JobInput(BaseModel):
    """Data collected from the *Generate Letter / Report* dialog."""

    url: str | None = Field(None, description="Job posting URL (optional)")
    job_markdown: str = Field(..., description="Full job description in markdown")
    detected_language: str = "en"
    company: str | None = None
    title: str | None = None
    location: str | None = None
    requirements: str | None = None


class SkillsExtractionResult(BaseModel):
    matching_skills: list[str] = []
    missing_skills: list[str] = []
    extra_skills: list[str] = []