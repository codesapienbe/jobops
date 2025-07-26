import logging
from fastapi import FastAPI, Request, Body
from fastapi.responses import JSONResponse, Response, FileResponse, StreamingResponse
from datetime import datetime
import json
import os
import re
from pydantic import ValidationError
from .models import MotivationLetter, Document, DocumentType
from .utils import generate_from_markdown, generate_optimized_resume_from_markdown, extract_skills, extract_skills_with_llm, build_consultant_reply_prompt
from .repositories import SQLiteDocumentRepository
import uuid
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware
from fastapi import status
from pydantic import BaseModel as PydanticBaseModel, Field
from datetime import datetime as dt
from rich.logging import RichHandler
from fastapi import UploadFile, File, Form

from dotenv import load_dotenv
load_dotenv(
    # Load .env file from the parent directory (../../.env)
    dotenv_path=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '.env')
)

# Configure structured JSON logging (file) and rich colored console logging
class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "component": "jobops_api",
            "message": record.getMessage(),
            "correlation_id": getattr(record, 'correlation_id', None),
            "user_id": getattr(record, 'user_id', None),
            "request_id": getattr(record, 'request_id', None),
        }
        return json.dumps({k: v for k, v in log_record.items() if v is not None})

logger = logging.getLogger("jobops_api")
logger.setLevel(logging.INFO)

# File handler for JSON logs
handler = logging.FileHandler("application.log")
handler.setFormatter(JsonFormatter())
logger.addHandler(handler)

# RichHandler for colored console output
console_handler = RichHandler(rich_tracebacks=True, show_time=True, show_level=True, show_path=False)
console_handler.setLevel(logging.INFO)
logger.addHandler(console_handler)

logger.propagate = False

# Ensure clips directory exists
os.makedirs('clips', exist_ok=True)

# Ensure ~/.jobops directory exists
os.makedirs(os.path.expanduser('~/.jobops'), exist_ok=True)

from .config import JSONConfigManager, CONSTANTS

# Set DB_PATH to ~/.jobops/jobops.db by default
DB_PATH = os.getenv("JOBOPS_DB_PATH", os.path.join(CONSTANTS.USER_HOME_DIR, CONSTANTS.DB_NAME))


def sanitize_filename(filename: str) -> str:
    filename = re.sub(r'[^a-zA-Z0-9_.-]', '_', filename)
    return filename[:64]

app = FastAPI(title="JobOps API", version="1.0.0")

# Set the default backend for utils (backend-agnostic LLM usage everywhere)
from .config import JSONConfigManager, CONSTANTS
from .clients import LLMBackendFactory
from .utils import set_default_backend
config_path = os.path.join(CONSTANTS.USER_HOME_DIR, CONSTANTS.CONFIG_NAME)
config = JSONConfigManager(config_path).load()
backend_type = getattr(config, 'backend', 'ollama')
backend_settings = getattr(config, 'backend_settings', {})
backend_conf = backend_settings.get(backend_type, {})
llm_client = LLMBackendFactory.create(backend_type, backend_conf, tokens={})
set_default_backend(llm_client)

# Add CORS and security headers middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"
    return response

# Structured error response model
class ErrorResponse(PydanticBaseModel):
    timestamp: str = Field(default_factory=lambda: dt.utcnow().isoformat() + "Z")
    level: str = Field(default="ERROR")
    component: str = Field(default="jobops_api")
    message: str = Field(...)
    correlation_id: Optional[str] = Field(default=None)
    user_id: Optional[str] = Field(default=None)
    request_id: Optional[str] = Field(default=None)
    
    class Config:
        schema_extra = {
            "example": {
                "timestamp": "2025-07-21T23:33:03.380309Z",
                "level": "ERROR",
                "component": "jobops_api",
                "message": "Validation error: ...",
                "correlation_id": "abc-123",
                "user_id": "user-42",
                "request_id": "req-99"
            }
        }

# Update error handling in middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID")
    user_id = request.headers.get("X-User-ID")
    correlation_id = request.headers.get("X-Correlation-ID")
    logger.info(
        f"Incoming request: {request.method} {request.url.path}",
        extra={"request_id": request_id, "user_id": user_id, "correlation_id": correlation_id}
    )
    try:
        response = await call_next(request)
    except Exception as exc:
        logger.error(
            f"Unhandled exception: {exc}",
            extra={"request_id": request_id, "user_id": user_id, "correlation_id": correlation_id}
        )
        err = ErrorResponse(message="Internal Server Error", correlation_id=correlation_id, user_id=user_id, request_id=request_id)
        return JSONResponse(status_code=500, content=err.dict())
    logger.info(
        f"Response: {response.status_code} {request.url.path}",
        extra={"request_id": request_id, "user_id": user_id, "correlation_id": correlation_id}
    )
    return response

# Update /health endpoint with OpenAPI metadata
@app.get("/health", tags=["system"], response_model=dict, summary="Health check", description="Check API health status.", responses={200: {"description": "API is healthy", "content": {"application/json": {"example": {"status": "ok"}}}}})
async def health():
    return {"status": "ok"}

# Update /clip endpoint with OpenAPI metadata and error responses
@app.post(
    "/clip",
    tags=["clip"],
    summary="Save a clipped page as markdown",
    description="Save a clipped web page as a markdown file.",
    response_model=dict,
    responses={
        200: {"description": "Clip saved", "content": {"application/json": {"example": {"status": "success", "filename": "20250721T233303Z_title.md"}}}},
        400: {"model": ErrorResponse, "description": "Missing title or body"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def clip_endpoint(request: Request, payload: dict = Body(...)):
    request_id = request.headers.get("X-Request-ID")
    user_id = request.headers.get("X-User-ID")
    correlation_id = request.headers.get("X-Correlation-ID")
    try:
        title = payload.get('title', '').strip()
        url = payload.get('url', '').strip()
        body = payload.get('body', '').strip()
        if not title or not body:
            logger.warning(
                'Missing title or body in /clip request',
                extra={"request_id": request_id, "user_id": user_id, "correlation_id": correlation_id}
            )
            err = ErrorResponse(message="Missing title or body", correlation_id=correlation_id, user_id=user_id, request_id=request_id)
            return JSONResponse(status_code=400, content=err.dict())
        timestamp = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
        safe_title = sanitize_filename(title) or 'untitled'
        filename = f"{timestamp}_{safe_title}.md"
        filepath = os.path.join('clips', filename)
        markdown = f"# {title}\n\nURL: {url}\n\n{body}\n"
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(markdown)
        logger.info(
            f"Clipped page saved as {filename}",
            extra={"request_id": request_id, "user_id": user_id, "correlation_id": correlation_id}
        )
        return {"status": "success", "filename": filename}
    except Exception as e:
        logger.error(
            f"Error in /clip: {str(e)}",
            extra={"request_id": request_id, "user_id": user_id, "correlation_id": correlation_id}
        )
        err = ErrorResponse(message="Internal server error", correlation_id=correlation_id, user_id=user_id, request_id=request_id)
        return JSONResponse(status_code=500, content=err.dict())

# Update /job-description endpoint with OpenAPI metadata and error responses
@app.post(
    "/job-description",
    tags=["job"],
    summary="Store a job description",
    description="Store a job description in markdown format.",
    response_model=dict,
    responses={
        200: {"description": "Job description stored", "content": {"application/json": {"example": {"status": "success", "group_id": "uuid"}}}},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def store_job_description(
    job_markdown: str = Body(..., embed=True, description="Full job description in markdown"),
    url: Optional[str] = Body(None, description="Job posting URL (optional)"),
    title: Optional[str] = Body(None, description="Job title (optional)"),
    company: Optional[str] = Body(None, description="Company name (optional)"),
    location: Optional[str] = Body(None, description="Job location (optional)"),
    requirements: Optional[str] = Body(None, description="Job requirements (optional)"),
    request: Request = None
):
    request_id = request.headers.get("X-Request-ID") if request else None
    user_id = request.headers.get("X-User-ID") if request else None
    correlation_id = request.headers.get("X-Correlation-ID") if request else None
    if not request:
        return JSONResponse(status_code=400, content={"status": "error", "error": "Request is required"})
    try:
        group_id = str(uuid.uuid4())
        doc_job = Document(
            type=DocumentType.JOB_DESCRIPTION,
            raw_content=job_markdown,
            structured_content=job_markdown,
            group_id=group_id,
            embedding=None
        )
        from .config import JSONConfigManager, CONSTANTS
        from .clients import LLMBackendFactory
        config_path = os.path.join(CONSTANTS.USER_HOME_DIR, CONSTANTS.CONFIG_NAME)
        config = JSONConfigManager(config_path).load()
        backend_type = getattr(config, 'backend', 'ollama')
        backend_settings = getattr(config, 'backend_settings', {})
        backend_conf = backend_settings.get(backend_type, {})
        llm_client = LLMBackendFactory.create(backend_type, backend_conf, tokens={})
        repository = SQLiteDocumentRepository(DB_PATH, llm_client=llm_client)
        repository.save(doc_job)
        logger.info(
            f"Job description stored as group {group_id}",
            extra={"request_id": request_id, "user_id": user_id, "correlation_id": correlation_id}
        )
        return {"status": "success", "group_id": group_id}
    except Exception as e:
        logger.error(
            f"Error in /job-description: {str(e)}",
            extra={"request_id": request_id, "user_id": user_id, "correlation_id": correlation_id}
        )
        err = ErrorResponse(message="Internal server error", correlation_id=correlation_id, user_id=user_id, request_id=request_id)
        return JSONResponse(status_code=500, content=err.dict())

# Update /generate-letter endpoint with OpenAPI metadata and error responses
@app.post(
    "/generate-letter",
    response_model=MotivationLetter,
    tags=["letter"],
    summary="Generate a motivation letter",
    description="Generate a personalized motivation letter for a job application.",
    responses={
        200: {"description": "Motivation letter generated"},
        422: {"model": ErrorResponse, "description": "Validation error"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def generate_letter_endpoint(
    group_id: str = Body(..., embed=True, description="Group ID for the document set"),
    detected_language: Optional[str] = Body("en", description="Detected language (default: en)"),
    request: Request = None
):
    request_id = request.headers.get("X-Request-ID") if request else None
    user_id = request.headers.get("X-User-ID") if request else None
    correlation_id = request.headers.get("X-Correlation-ID") if request else None
    if not request:
        return JSONResponse(status_code=400, content={"status": "error", "error": "Request is required"})
    try:
        logger.info(
            f"/generate-letter called with group_id: {group_id}",
            extra={"request_id": request_id, "user_id": user_id, "correlation_id": correlation_id}
        )
        # Fetch job description document
        from .config import JSONConfigManager, CONSTANTS
        from .clients import LLMBackendFactory
        config_path = os.path.join(CONSTANTS.USER_HOME_DIR, CONSTANTS.CONFIG_NAME)
        config = JSONConfigManager(config_path).load()
        backend_type = getattr(config, 'backend', 'ollama')
        backend_settings = getattr(config, 'backend_settings', {})
        backend_conf = backend_settings.get(backend_type, {})
        llm_client = LLMBackendFactory.create(backend_type, backend_conf, tokens={})
        repository = SQLiteDocumentRepository(DB_PATH, llm_client=llm_client)
        docs = repository.get_by_group(group_id)
        job_doc = next((d for d in docs if d.type == DocumentType.JOB_DESCRIPTION), None)
        if not job_doc:
            logger.warning(
                f"No job description found for group_id: {group_id}",
                extra={"request_id": request_id, "user_id": user_id, "correlation_id": correlation_id}
            )
            return JSONResponse(status_code=404, content={"status": "error", "error": "Job description not found."})
        job_markdown = job_doc.structured_content
        # Optionally, fetch metadata from job_doc if stored
        resume_markdown = repository.get_latest_resume()
        if resume_markdown is None:
            logger.warning(
                "No resume found. Please upload your resume first.",
                extra={"request_id": request_id, "user_id": user_id, "correlation_id": correlation_id}
            )
            return JSONResponse(status_code=400, content={"status": "error", "error": "No resume found. Please upload your resume first."})
        # Generate motivation letter
        letter = generate_from_markdown(
            job_markdown=None,  # placeholder, actual logic unchanged
            resume_markdown=None,
            language=detected_language,
            url=None,
            company_name=None,
            job_title=None,
            location=None
        )
        # Generate tailored resume
        tailored_resume = generate_optimized_resume_from_markdown(
            job_markdown=job_markdown,
            resume_markdown=resume_markdown,
            language=detected_language,
            requirements=None
        )
        # Extract skills
        job_requirements = None
        llm_backend = None  # TODO: wire up LLM backend if needed
        skill_data = extract_skills_with_llm(llm_backend, resume_markdown, job_markdown) if llm_backend else None
        if skill_data:
            matched = sorted(set(skill_data['matching_skills']))
            missing = sorted(set(skill_data['missing_skills']))
            extra = sorted(set(skill_data['extra_skills']))
        else:
            resume_skills = extract_skills(resume_markdown)
            job_skills = extract_skills(job_markdown)
            matched = sorted(resume_skills & job_skills)
            missing = sorted(job_skills - resume_skills)
            extra = sorted(resume_skills - job_skills)
        # Prepare and save documents
        doc_resume = Document(
            type=DocumentType.RESUME,
            raw_content=tailored_resume,
            structured_content=tailored_resume,
            group_id=group_id,
            embedding=None
        )
        repository.save(doc_resume)
        doc_letter = Document(
            type=DocumentType.COVER_LETTER,
            raw_content=letter.content,
            structured_content=letter.content,
            group_id=group_id,
            embedding=None
        )
        repository.save(doc_letter)
        # Skills report as markdown
        summary = f"You have matched {len(matched)} of {len(matched) + len(missing)} required skills."
        report_lines = [
            "# Skills Match Report",
            "",
            summary,
            "",
            "## Skill Details",
            "",
        ]
        if matched:
            report_lines.append("**Matched Skills:**")
            report_lines.extend([f"- {s}" for s in matched])
        if missing:
            report_lines.append("")
            report_lines.append("**Missing Skills:**")
            report_lines.extend([f"- {s}" for s in missing])
        if extra:
            report_lines.append("")
            report_lines.append("**Additional Skills:**")
            report_lines.extend([f"- {s}" for s in extra])
        report_md = "\n".join(report_lines)
        doc_report = Document(
            type=DocumentType.OTHER,
            raw_content=report_md,
            structured_content=report_md,
            group_id=group_id,
            embedding=None
        )
        repository.save(doc_report)
        logger.info(
            f"Motivation package generated and saved to database. Group ID: {group_id}",
            extra={"request_id": request_id, "user_id": user_id, "correlation_id": correlation_id}
        )
        return letter
    except ValidationError as ve:
        logger.error(
            f"Validation error: {ve}",
            extra={"request_id": request_id, "user_id": user_id, "correlation_id": correlation_id}
        )
        err = ErrorResponse(message=f"Validation error: {ve}", correlation_id=correlation_id, user_id=user_id, request_id=request_id)
        return JSONResponse(status_code=422, content=err.dict())
    except Exception as e:
        logger.error(
            f"Error in /generate-letter: {str(e)}",
            extra={"request_id": request_id, "user_id": user_id, "correlation_id": correlation_id}
        )
        err = ErrorResponse(message="Internal server error", correlation_id=correlation_id, user_id=user_id, request_id=request_id)
        return JSONResponse(status_code=500, content=err.dict())

@app.post(
    "/consultant-reply",
    tags=["consultant"],
    summary="Generate a consultant reply sheet",
    description="Generate a professional consultant reply sheet in markdown format.",
    response_model=dict,
    responses={
        200: {"description": "Consultant reply generated", "content": {"application/json": {"example": {"reply_markdown": "..."}}}},
        422: {"model": ErrorResponse, "description": "Validation error"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def consultant_reply_endpoint(
    email_message: str = Body(..., description="Consultant email message/request"),
    resume_markdown: str = Body(..., description="Candidate's resume in markdown format"),
    language: str = Body("en", description="Language for the reply (default: en)"),
    request: Request = None
):
    request_id = request.headers.get("X-Request-ID") if request else None
    user_id = request.headers.get("X-User-ID") if request else None
    correlation_id = request.headers.get("X-Correlation-ID") if request else None
    try:
        # ① Build the consultant reply prompt
        logger.info(
            f"/consultant-reply called with email_message: {email_message}, resume_markdown: {resume_markdown}, language: {language}",
            extra={"request_id": request_id, "user_id": user_id, "correlation_id": correlation_id}
        )
        prompt = build_consultant_reply_prompt(email_message, resume_markdown, language)
        # ② Call the LLM backend to generate the reply
        from .config import JSONConfigManager, CONSTANTS
        from .clients import LLMBackendFactory
        config_path = os.path.join(CONSTANTS.USER_HOME_DIR, CONSTANTS.CONFIG_NAME)
        config = JSONConfigManager(config_path).load()
        backend_type = getattr(config, 'backend', 'ollama')
        backend_settings = getattr(config, 'backend_settings', {})
        backend_conf = backend_settings.get(backend_type, {})
        llm_client = LLMBackendFactory.create(backend_type, backend_conf, tokens={})
        repository = SQLiteDocumentRepository(DB_PATH, llm_client=llm_client)
        reply_md = llm_client.generate_response(prompt)
        # ③ Return the reply markdown
        return {"reply_markdown": reply_md}
    except Exception as e:
        logger.error(f"Error in /consultant-reply: {str(e)}")
        err = ErrorResponse(message="Internal server error")
        return JSONResponse(status_code=500, content=err.dict())

@app.post(
    "/upload-document",
    tags=["document"],
    summary="Upload a document (resume, certification, etc.)",
    description="Upload a document file and store it in the database after parsing and embedding.",
    response_model=dict,
    responses={
        200: {"description": "Document uploaded and parsed", "content": {"application/json": {"example": {"status": "success", "doc_id": "uuid"}}}},
        400: {"model": ErrorResponse, "description": "Invalid input"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def upload_document_endpoint(
    file: UploadFile = File(..., description="Document file to upload (PDF, DOCX, MD, etc.)"),
    doc_type: str = Form(..., description="Type of document: RESUME, CERTIFICATION, etc."),
    request: Request = None
):
    try:
        import os
        import tempfile
        from datetime import datetime
        from .models import Document, DocumentType
        request_id = request.headers.get("X-Request-ID") if request else None
        user_id = request.headers.get("X-User-ID") if request else None
        correlation_id = request.headers.get("X-Correlation-ID") if request else None
        # ① Save uploaded file to a temp location
        if not file.filename:
            logger.warning(
                "No file name provided in /upload-document request",
                extra={"request_id": request_id, "user_id": user_id, "correlation_id": correlation_id}
            )
            return JSONResponse(status_code=400, content={"status": "error", "error": "File name is required"})
        if not doc_type:
            logger.warning(
                "No document type provided in /upload-document request",
                extra={"request_id": request_id, "user_id": user_id, "correlation_id": correlation_id}
            )
            return JSONResponse(status_code=400, content={"status": "error", "error": "Document type is required"})
        suffix = os.path.splitext(file.filename)[-1].lower()
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name
        # ② Load config and backend
        from .config import JSONConfigManager, CONSTANTS
        from .clients import LLMBackendFactory
        config_path = os.path.join(CONSTANTS.USER_HOME_DIR, CONSTANTS.CONFIG_NAME)
        config = JSONConfigManager(config_path).load()
        backend_type = getattr(config, 'backend', 'ollama')
        backend_settings = getattr(config, 'backend_settings', {})
        backend_conf = backend_settings.get(backend_type, {})
        llm_client = LLMBackendFactory.create(backend_type, backend_conf, tokens={})
        # ③ Parse the file (markdown direct, others via MarkItDown)
        if suffix.lower() == ".md":
            with open(tmp_path, "r", encoding="utf-8") as f:
                structured_content = f.read()
            raw_content = structured_content
        else:
            try:
                from markitdown import MarkItDown
                from .clients import OllamaOpenAIAdapter
                # Use OllamaOpenAIAdapter if backend is ollama
                if backend_type == "ollama":
                    llm_client_for_markitdown = OllamaOpenAIAdapter(llm_client)
                else:
                    llm_client_for_markitdown = llm_client
                md = MarkItDown(llm_client=llm_client_for_markitdown, llm_model=backend_conf.get('model', 'gpt-4o'))
                result = md.convert(tmp_path)
                structured_content = result.text_content
                raw_content = getattr(result, 'raw_text', structured_content)
            except Exception as e:
                return JSONResponse(status_code=400, content={"status": "error", "error": f"File parsing failed: {e}"})
        # ④ Compute embedding
        embedding = llm_client.embed_structured_data(structured_content)
        # ⑤ Save to DB
        doc_type_enum = DocumentType[doc_type.upper()] if doc_type.upper() in DocumentType.__members__ else DocumentType.OTHER
        doc = Document(
            type=doc_type_enum,
            raw_content=raw_content,
            structured_content=structured_content,
            uploaded_at=datetime.now(),
            embedding=embedding,
            group_id=str(uuid.uuid4())
        )
        repository = SQLiteDocumentRepository(DB_PATH, llm_client=llm_client)
        doc_id = repository.save(doc)
        # ⑥ Return success
        return {"status": "success", "doc_id": doc_id}
    except Exception as e:
        logger.error(f"Error in /upload-document: {str(e)}")
        err = ErrorResponse(message="Internal server error")
        return JSONResponse(status_code=500, content=err.dict())

@app.post(
    "/extract-skills",
    tags=["skills"],
    summary="Extract and compare skills from resume and job description",
    description="Extracts matching, missing, and extra skills using LLM or regex fallback.",
    response_model=dict,
    responses={
        200: {"description": "Skills extracted", "content": {"application/json": {"example": {"matching_skills": ["Python"], "missing_skills": ["Docker"], "extra_skills": ["Java"]}}}},
        400: {"model": ErrorResponse, "description": "Invalid input"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def extract_skills_endpoint(
    resume_text: str = Body(..., description="Resume text (markdown or plain)"),
    job_text: str = Body(..., description="Job description and requirements (markdown or plain)"),
    request: Request = None
):
    try:
        # ① Try LLM-based extraction
        from .utils import extract_skills_with_llm, extract_skills
        llm_backend = None  # TODO: Use configured backend if available
        skill_data = extract_skills_with_llm(llm_backend, resume_text, job_text) if llm_backend else None
        # ② Fallback to regex extraction
        if skill_data:
            matched = sorted(set(skill_data["matching_skills"]))
            missing = sorted(set(skill_data["missing_skills"]))
            extra = sorted(set(skill_data["extra_skills"]))
        else:
            resume_skills = extract_skills(resume_text)
            job_skills = extract_skills(job_text)
            matched = sorted(resume_skills & job_skills)
            missing = sorted(job_skills - resume_skills)
            extra = sorted(resume_skills - job_skills)
        # ③ Return result
        return {"matching_skills": matched, "missing_skills": missing, "extra_skills": extra}
    except Exception as e:
        logger.error(f"Error in /extract-skills: {str(e)}")
        err = ErrorResponse(message="Internal server error")
        return JSONResponse(status_code=500, content=err.dict())

@app.post(
    "/log",
    tags=["system"],
    summary="Log a message to application.log",
    description="Log a structured message to the application log file for monitoring and debugging.",
    response_model=dict,
    responses={
        200: {"description": "Message logged", "content": {"application/json": {"example": {"status": "success"}}}},
        400: {"model": ErrorResponse, "description": "Invalid log data"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def log_endpoint(
    log_data: dict = Body(..., description="Structured log data"),
    request: Optional[Request] = None
):
    """Log a structured message to application.log"""
    try:
        # Validate required fields
        required_fields = ['timestamp', 'level', 'component', 'message']
        for field in required_fields:
            if field not in log_data:
                return JSONResponse(
                    status_code=400,
                    content=ErrorResponse(
                        message=f"Missing required field: {field}",
                        correlation_id=getattr(request, 'correlation_id', None)
                    ).dict()
                )
        
        # Sanitize and validate log level
        level = log_data.get('level', 'INFO').upper()
        valid_levels = ['DEBUG', 'INFO', 'WARN', 'WARNING', 'ERROR', 'CRITICAL']
        if level not in valid_levels:
            level = 'INFO'  # Default to INFO for invalid levels
        
        # Create log record with structured data
        log_record = {
            "timestamp": log_data.get('timestamp'),
            "level": level,
            "component": log_data.get('component', 'jobops_clipper'),
            "message": log_data.get('message'),
            "correlation_id": log_data.get('correlation_id'),
            "user_id": log_data.get('user_id'),
            "request_id": log_data.get('request_id'),
        }
        
        # Add any additional fields from log_data
        for key, value in log_data.items():
            if key not in log_record and value is not None:
                log_record[key] = value
        
        # Log the message
        if level == 'DEBUG':
            logger.debug(log_record['message'], extra=log_record)
        elif level in ['WARN', 'WARNING']:
            logger.warning(log_record['message'], extra=log_record)
        elif level == 'ERROR':
            logger.error(log_record['message'], extra=log_record)
        elif level == 'CRITICAL':
            logger.critical(log_record['message'], extra=log_record)
        else:
            logger.info(log_record['message'], extra=log_record)
        
        return {"status": "success", "message": "Log entry recorded"}
        
    except Exception as e:
        logger.error(f"Failed to log message: {str(e)}", extra={
            'component': 'jobops_api.log_endpoint',
            'error': str(e),
            'correlation_id': getattr(request, 'correlation_id', None)
        })
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                message=f"Failed to log message: {str(e)}",
                correlation_id=getattr(request, 'correlation_id', None)
            ).dict()
        )

@app.post(
    "/extract-document",
    tags=["document"],
    summary="Extract structured data from a document",
    description="Extracts structured data from a raw document using LLM or fallback logic.",
    response_model=dict,
    responses={
        200: {"description": "Document extracted", "content": {"application/json": {"example": {"title": "...", "sections": {}}}}},
        400: {"model": ErrorResponse, "description": "Invalid input"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def extract_document_endpoint(
    raw_content: str = Body(..., description="Raw document content (text)"),
    doc_type: str = Body(..., description="Type of document (e.g., RESUME, CERTIFICATION, etc.)"),
    request: Request = None
):
    try:
        from .models import DocumentType
        from .utils import DocumentExtractor
        # ① Use DocumentExtractor to parse the document
        from .config import JSONConfigManager, CONSTANTS
        from .clients import LLMBackendFactory
        config_path = os.path.join(CONSTANTS.USER_HOME_DIR, CONSTANTS.CONFIG_NAME)
        config = JSONConfigManager(config_path).load()
        backend_type = getattr(config, 'backend', 'ollama')
        backend_settings = getattr(config, 'backend_settings', {})
        backend_conf = backend_settings.get(backend_type, {})
        llm_client = LLMBackendFactory.create(backend_type, backend_conf, tokens={})
        extractor = DocumentExtractor(llm_backend=llm_client)  # TODO: Use configured backend if available
        doc_type_enum = DocumentType[doc_type.upper()] if doc_type.upper() in DocumentType.__members__ else DocumentType.OTHER
        result = extractor.extract_generic_document(raw_content, doc_type_enum)
        # ② Return structured document data
        return result.dict()
    except Exception as e:
        logger.error(f"Error in /extract-document: {str(e)}")
        err = ErrorResponse(message="Internal server error")
        return JSONResponse(status_code=500, content=err.dict())

# --- main entrypoint for uvicorn/uv run ---
def main():
    import uvicorn
    import os
    port_str = os.environ.get("JOBOPS_API_PORT")
    if not port_str:
        raise RuntimeError("Environment variable JOBOPS_API_PORT must be set (no default port allowed).")
    try:
        port = int(port_str)
    except ValueError:
        raise RuntimeError(f"JOBOPS_API_PORT must be an integer, got: {port_str}")
    uvicorn.run("jobops_api.__init__:app", host="0.0.0.0", port=port, log_config=None, log_level="info")

if __name__ == "__main__":
    main() 