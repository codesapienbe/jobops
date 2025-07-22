import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from datetime import datetime
import json
import os
import re
from fastapi import Body
from pydantic import ValidationError
from .models import MotivationLetter, Document, DocumentType
from .utils import generate_from_markdown, generate_optimized_resume_from_markdown, extract_skills, extract_skills_with_llm, build_consultant_reply_prompt
from .repositories import SQLiteDocumentRepository
import uuid
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware
from fastapi import status
from pydantic import BaseModel as PydanticBaseModel, Field as PydanticField
from datetime import datetime as dt
from rich.logging import RichHandler
from pydantic import Field
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

# Dependency: get repository instance
DB_PATH = os.getenv("JOBOPS_DB_PATH", "jobopsdb.sqlite3")
repository = SQLiteDocumentRepository(DB_PATH)


def sanitize_filename(filename: str) -> str:
    filename = re.sub(r'[^a-zA-Z0-9_.-]', '_', filename)
    return filename[:64]

app = FastAPI(title="JobOps API", version="1.0.0")

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
    timestamp: str = Field(default_factory=lambda: dt.utcnow().isoformat() + "Z", example="2025-07-21T23:33:03.380309Z")
    level: str = Field(default="ERROR", example="ERROR")
    component: str = Field(default="jobops_api", example="jobops_api")
    message: str = Field(..., example="Validation error: ...")
    correlation_id: str | None = Field(default=None, example="abc-123")
    user_id: str | None = Field(default=None, example="user-42")
    request_id: str | None = Field(default=None, example="req-99")

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
    try:
        group_id = str(uuid.uuid4())
        doc_job = Document(
            type=DocumentType.JOB_DESCRIPTION,
            raw_content=job_markdown,
            structured_content=job_markdown,
            group_id=group_id
        )
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
    try:
        logger.info(
            f"/generate-letter called with group_id: {group_id}",
            extra={"request_id": request_id, "user_id": user_id, "correlation_id": correlation_id}
        )
        # Fetch job description document
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
            group_id=group_id
        )
        repository.save(doc_resume)
        doc_letter = Document(
            type=DocumentType.COVER_LETTER,
            raw_content=letter.content,
            structured_content=letter.content,
            group_id=group_id
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
            group_id=group_id
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
    try:
        # ① Build the consultant reply prompt
        prompt = build_consultant_reply_prompt(email_message, resume_markdown, language)
        # ② Call the LLM backend to generate the reply
        from .clients import OllamaBackend
        backend = OllamaBackend()  # TODO: Use configured backend
        reply_md = backend.generate_response(prompt)
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
        # ① Save uploaded file to a temp location
        suffix = os.path.splitext(file.filename)[-1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name
        # ② Parse the file (markdown direct, others via MarkItDown)
        if suffix.lower() == ".md":
            with open(tmp_path, "r", encoding="utf-8") as f:
                structured_content = f.read()
            raw_content = structured_content
        else:
            try:
                from markitdown import MarkItDown
                from openai import OpenAI
                # TODO: Use configured backend for LLM
                llm_client = OpenAI()
                md = MarkItDown(llm_client=llm_client, llm_model="gpt-4o")
                result = md.convert(tmp_path)
                structured_content = result.text_content
                raw_content = getattr(result, 'raw_text', structured_content)
            except Exception as e:
                return JSONResponse(status_code=400, content={"status": "error", "error": f"File parsing failed: {e}"})
        # ③ Compute embedding
        from .clients import embed_structured_data
        embedding = embed_structured_data(structured_content)
        # ④ Save to DB
        doc_type_enum = DocumentType[doc_type.upper()] if doc_type.upper() in DocumentType.__members__ else DocumentType.OTHER
        doc = Document(
            type=doc_type_enum,
            raw_content=raw_content,
            structured_content=structured_content,
            uploaded_at=datetime.now(),
            embedding=embedding,
            group_id=str(uuid.uuid4())
        )
        doc_id = repository.save(doc)
        # ⑤ Return success
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
        extractor = DocumentExtractor(llm_backend=None)  # TODO: Use configured backend if available
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