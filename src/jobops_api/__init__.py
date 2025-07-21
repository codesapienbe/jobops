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
from .utils import generate_from_markdown, generate_optimized_resume_from_markdown, extract_skills, extract_skills_with_llm
from .repositories import SQLiteDocumentRepository
import uuid
from typing import Optional

# Configure structured JSON logging
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
handler = logging.FileHandler("application.log")
handler.setFormatter(JsonFormatter())
logger.setLevel(logging.INFO)
logger.addHandler(handler)
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
        return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})
    logger.info(
        f"Response: {response.status_code} {request.url.path}",
        extra={"request_id": request_id, "user_id": user_id, "correlation_id": correlation_id}
    )
    return response

@app.get("/health", tags=["system"])
async def health():
    return {"status": "ok"}

@app.post("/clip", tags=["clip"])
async def clip_endpoint(request: Request, payload: dict = Body(...)):
    request_id = request.headers.get("X-Request-ID")
    user_id = request.headers.get("X-User-ID")
    correlation_id = request.headers.get("X-Correlation-ID")
    try:
        title = payload.get('title', '').strip()
        url = payload.get('url', '').strip()
        body = payload.get('body', '').strip()

        # Basic validation
        if not title or not body:
            logger.warning(
                'Missing title or body in /clip request',
                extra={"request_id": request_id, "user_id": user_id, "correlation_id": correlation_id}
            )
            return JSONResponse(status_code=400, content={"status": "error", "error": "Missing title or body"})

        # Sanitize filename
        timestamp = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
        safe_title = sanitize_filename(title) or 'untitled'
        filename = f"{timestamp}_{safe_title}.md"
        filepath = os.path.join('clips', filename)

        # Compose markdown content
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
        return JSONResponse(status_code=500, content={"status": "error", "error": "Internal server error"})

@app.post("/job-description", tags=["job"])
async def store_job_description(
    job_markdown: str = Body(..., embed=True),
    url: Optional[str] = Body(None),
    title: Optional[str] = Body(None),
    company: Optional[str] = Body(None),
    location: Optional[str] = Body(None),
    requirements: Optional[str] = Body(None),
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
            f"Job description stored. Group ID: {group_id}",
            extra={"request_id": request_id, "user_id": user_id, "correlation_id": correlation_id}
        )
        return {"status": "success", "group_id": group_id}
    except Exception as e:
        logger.error(
            f"Error in /job-description: {str(e)}",
            extra={"request_id": request_id, "user_id": user_id, "correlation_id": correlation_id}
        )
        return JSONResponse(status_code=500, content={"status": "error", "error": "Internal server error"})

@app.post("/generate-letter", response_model=MotivationLetter, tags=["letter"])
async def generate_letter_endpoint(
    group_id: str = Body(..., embed=True),
    detected_language: Optional[str] = Body("en"),
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
            job_markdown=job_markdown,
            resume_markdown=resume_markdown,
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
        return JSONResponse(status_code=422, content={"status": "error", "error": str(ve)})
    except Exception as e:
        logger.error(
            f"Error in /generate-letter: {str(e)}",
            extra={"request_id": request_id, "user_id": user_id, "correlation_id": correlation_id}
        )
        return JSONResponse(status_code=500, content={"status": "error", "error": "Internal server error"})

# --- main entrypoint for uvicorn/uv run ---
def main():
    import uvicorn
    uvicorn.run("jobops_api.__init__:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)), log_config=None, log_level="info")

if __name__ == "__main__":
    main() 