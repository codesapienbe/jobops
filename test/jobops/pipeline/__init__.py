import pytest
import numpy as np
import jobops.pipeline as pipeline
from jobops.pipeline import run_pipeline
from jobops.repositories import SQLiteDocumentRepository
from jobops.models import Document, DocumentType

@pytest.fixture(autouse=True)
def fake_embed(monkeypatch):
    """Stub embed_structured_data to return deterministic vectors based on keywords."""
    def fake_embed_fn(text):
        text_low = text.lower()
        if 'python' in text_low:
            return np.array([1.0, 0.0])
        if 'java' in text_low:
            return np.array([0.0, 1.0])
        return np.array([0.0, 0.0])
    monkeypatch.setattr(pipeline, 'embed_structured_data', fake_embed_fn)

@pytest.fixture
def temp_db(tmp_path, request):
    """Create a temporary SQLite DB, provide a function to populate it, and remove on teardown."""
    db_file = tmp_path / "test.db"
    repo = SQLiteDocumentRepository(str(db_file))
    def _create(docs):
        for doc in docs:
            repo.save(doc)
        return str(db_file)
    def _cleanup():
        if db_file.exists():
            db_file.unlink()
    request.addfinalizer(_cleanup)
    return _create

def test_pipeline_recommends_python_resume(temp_db):
    # Prepare sample resumes
    docs = [
        Document(
            type=DocumentType.RESUME,
            raw_content="""EXPERIENCE
Senior Python Developer
- Developed and maintained multiple Python applications
- Used Django and Flask frameworks extensively
- Implemented REST APIs and microservices
- Worked with PostgreSQL and MongoDB databases""",
            structured_content="""Python developer with 5+ years experience in web development.
Expertise in Django, Flask, REST APIs, and database design.
Strong background in microservices architecture and cloud deployment."""
        ),
        Document(
            type=DocumentType.RESUME,
            raw_content="""EXPERIENCE
Java Developer
- Built enterprise applications using Spring Boot
- Developed microservices architecture
- Worked with Oracle and MySQL databases
- Implemented CI/CD pipelines""",
            structured_content="""Java developer with 4 years of enterprise application development.
Proficient in Spring Boot, microservices, and database management.
Experience with CI/CD and cloud platforms."""
        ),
    ]
    db_path = temp_db(docs)
    job_desc = "Looking for a Python developer with web development experience"

    # Run pipeline and get top recommendation
    recommended = run_pipeline(job_desc, db_path=db_path, top_k=1)

    assert len(recommended) == 1, "Expected one recommended resume"
    assert "python" in recommended[0].structured_content.lower(), "The recommended resume should relate to Python"

def test_pipeline_recommends_java_resume(temp_db):
    # Prepare sample resumes
    docs = [
        Document(
            type=DocumentType.RESUME,
            raw_content="""EXPERIENCE
Python Developer
- Built data processing pipelines
- Developed machine learning models
- Used TensorFlow and PyTorch
- Implemented REST APIs""",
            structured_content="""Python developer specializing in data science and machine learning.
Expert in TensorFlow, PyTorch, and data processing pipelines.
Experience with REST APIs and cloud platforms."""
        ),
        Document(
            type=DocumentType.RESUME,
            raw_content="""EXPERIENCE
Senior Java Developer
- Led development of enterprise applications
- Architected microservices solutions
- Managed team of 5 developers
- Implemented CI/CD pipelines""",
            structured_content="""Senior Java developer with 8+ years of enterprise experience.
Expert in microservices architecture and team leadership.
Strong background in CI/CD and cloud deployment."""
        ),
    ]
    db_path = temp_db(docs)
    job_desc = "Looking for a senior Java developer with enterprise experience"
    # Run pipeline and get top recommendation
    recommended = run_pipeline(job_desc, db_path=db_path, top_k=1)
    assert len(recommended) == 1, "Expected one recommended resume"
    assert "java" in recommended[0].structured_content.lower(), "The recommended resume should relate to Java"

def test_pipeline_recommends_python_resume_with_top_k_2(temp_db):
    # Prepare sample resumes
    docs = [
        Document(
            type=DocumentType.RESUME,
            raw_content="""EXPERIENCE
Python Developer
- Developed web applications using Django
- Built REST APIs and microservices
- Worked with PostgreSQL and Redis
- Implemented automated testing""",
            structured_content="""Python developer with 3 years of web development experience.
Expert in Django, REST APIs, and database design.
Strong background in testing and deployment."""
        ),
        Document(
            type=DocumentType.RESUME,
            raw_content="""EXPERIENCE
Java Developer
- Built enterprise applications
- Developed microservices
- Worked with Spring Boot
- Implemented CI/CD""",
            structured_content="""Java developer with 4 years of enterprise development.
Proficient in Spring Boot and microservices architecture.
Experience with CI/CD and cloud platforms."""
        ),
    ]
    db_path = temp_db(docs)
    job_desc = "Looking for a developer with web development experience"

    # Run pipeline and get top recommendation
    recommended = run_pipeline(job_desc, db_path=db_path, top_k=2)

    assert len(recommended) == 2, "Expected two recommended resumes"
    contents = [doc.structured_content.lower() for doc in recommended]
    assert any("python" in c for c in contents), "One recommended resume should relate to Python"
    assert any("java" in c for c in contents), "One recommended resume should relate to Java"

def test_pipeline_recommends_java_resume_with_top_k_2(temp_db):
    # Prepare sample resumes
    docs = [
        Document(
            type=DocumentType.RESUME,
            raw_content="""EXPERIENCE
Python Developer
- Built data science applications
- Developed machine learning models
- Used TensorFlow and PyTorch
- Implemented data pipelines""",
            structured_content="""Python developer specializing in data science and ML.
Expert in TensorFlow, PyTorch, and data processing.
Experience with cloud platforms and big data."""
        ),
        Document(
            type=DocumentType.RESUME,
            raw_content="""EXPERIENCE
Senior Java Developer
- Led enterprise application development
- Architected microservices solutions
- Managed development team
- Implemented CI/CD pipelines""",
            structured_content="""Senior Java developer with enterprise experience.
Expert in microservices and team leadership.
Strong background in CI/CD and cloud deployment."""
        ),
    ]
    db_path = temp_db(docs)
    job_desc = "Looking for a senior developer with enterprise experience"

    # Run pipeline and get top recommendation
    recommended = run_pipeline(job_desc, db_path=db_path, top_k=2)

    assert len(recommended) == 2, "Expected two recommended resumes"
    contents = [doc.structured_content.lower() for doc in recommended]
    assert any("java" in c for c in contents), "One recommended resume should relate to Java"
    assert any("python" in c for c in contents), "One recommended resume should relate to Python"

def test_pipeline_recommends_no_resume(temp_db):
    # Prepare sample resumes
    docs = [
        Document(
            type=DocumentType.RESUME,
            raw_content="""EXPERIENCE
Python Developer
- Developed web applications
- Built REST APIs
- Used Django and Flask
- Implemented testing""",
            structured_content="""Python developer with web development experience.
Expert in Django, Flask, and REST APIs.
Strong background in testing and deployment."""
        ),
        Document(
            type=DocumentType.RESUME,
            raw_content="""EXPERIENCE
Java Developer
- Built enterprise applications
- Developed microservices
- Used Spring Boot
- Implemented CI/CD""",
            structured_content="""Java developer with enterprise experience.
Proficient in Spring Boot and microservices.
Experience with CI/CD and cloud platforms."""
        ),
    ]
    db_path = temp_db(docs)
    job_desc = "Looking for a C# developer with .NET experience"

    # Run pipeline and get top recommendation
    recommended = run_pipeline(job_desc, db_path=db_path, top_k=1)

    assert len(recommended) == 1, "Expected one recommended resume based on embedding similarity"
