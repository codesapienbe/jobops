#!/usr/bin/env python3
"""
AI Motivation Letter Generator
A clean, maintainable application for generating motivation letters.
"""

import os
import json
import logging
import sqlite3
import sys
import threading
import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Protocol, Union
from datetime import datetime
from enum import Enum
from dataclasses import dataclass
from pathlib import Path
import webbrowser
import io

import psutil
import requests
from bs4 import BeautifulSoup
from plyer import notification
import pystray
from PIL import Image, ImageDraw
from dotenv import load_dotenv

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

try:
    import pdfplumber
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

try:
    import crawl4ai
    from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BrowserConfig, CacheMode
    from crawl4ai.content_filter_strategy import PruningContentFilter
    from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
    CRAWL4AI_AVAILABLE = True
except ImportError:
    CRAWL4AI_AVAILABLE = False

try:
    import markdown2
    MARKDOWN2_AVAILABLE = True
except ImportError:
    MARKDOWN2_AVAILABLE = False

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    from reportlab.lib.utils import simpleSplit
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

load_dotenv()

from pydantic import BaseModel, Field, validator, root_validator
from uuid import uuid4

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

class Language(BaseModel):
    name: Optional[str] = Field(None, description="Language name")
    proficiency: Optional[str] = Field(None, description="Proficiency level")

class Resume(BaseModel):
    id: Optional[str] = Field(default_factory=lambda: str(uuid4()))
    personal_info: PersonalInfo = Field(default_factory=PersonalInfo)
    summary: Optional[str] = Field(None, description="Professional summary or objective")
    work_experience: List[WorkExperience] = Field(default_factory=list)
    education: List[Education] = Field(default_factory=list)
    technical_skills: List[str] = Field(default_factory=list)
    soft_skills: List[str] = Field(default_factory=list)
    projects: List[Project] = Field(default_factory=list)
    certifications: List[Certification] = Field(default_factory=list)
    languages: List[Language] = Field(default_factory=list)
    publications: List[str] = Field(default_factory=list)
    awards: List[str] = Field(default_factory=list)
    volunteer_experience: List[str] = Field(default_factory=list)
    interests: List[str] = Field(default_factory=list)
    references: Optional[str] = Field(None, description="References section")
    additional_sections: Dict[str, Any] = Field(default_factory=dict, description="Any other sections")
    created_at: datetime = Field(default_factory=datetime.now)
    
    @root_validator(pre=True)
    def handle_invalid_values(cls, values):
        for key, value in values.items():
            if isinstance(value, str) and value.lower() in {'n/a', 'none', '', 'null'}:
                values[key] = None
        return values

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
    scraped_at: datetime = Field(default_factory=datetime.now)
    company_profile_url: Optional[str] = None
    company_profile: Optional[str] = None
    
    @validator('url')
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
    filename: Optional[str] = None
    raw_content: str
    structured_content: str
    uploaded_at: datetime = Field(default_factory=datetime.now)
    reasoning_analysis: Optional[str] = None

class MotivationLetter(BaseModel):
    id: Optional[str] = Field(default_factory=lambda: str(uuid4()))
    job_data: JobData
    resume: Resume
    content: str
    language: str = "en"
    generated_at: datetime = Field(default_factory=datetime.now)

class AppConfig(BaseModel):
    backend: str = "ollama"
    backend_settings: Dict[str, Dict[str, Any]] = {
        'ollama': {'model': 'qwen3:0.6b', 'base_url': 'http://localhost:11434'},
        'openai': {'model': 'gpt-4-turbo-preview'},
        'groq': {'model': 'mixtral-8x7b-32768'}
    }
    app_settings: Dict[str, Any] = {
        'language': 'en',
        'output_format': 'markdown'
    }
    sqlite_timeout: float = 30.0

class LLMBackend(Protocol):
    def generate_response(self, prompt: str, system_prompt: Optional[str] = None) -> str: ...
    def health_check(self) -> bool: ...

class DocumentRepository(Protocol):
    def save(self, document: Document) -> str: ...
    def get_by_id(self, doc_id: str) -> Optional[Document]: ...
    def get_by_type(self, doc_type: DocumentType) -> List[Document]: ...
    def get_latest_resume(self) -> Optional[Resume]: ...
    def delete(self, doc_id: str) -> bool: ...

class JobScraper(Protocol):
    def scrape_job_description(self, url: str) -> JobData: ...

class LetterGenerator(Protocol):
    def generate(self, job_data: JobData, resume: Resume, language: str = "en") -> MotivationLetter: ...

class ConfigManager(Protocol):
    def load(self) -> AppConfig: ...
    def save(self, config: AppConfig) -> None: ...

class NotificationService(Protocol):
    def notify(self, title: str, message: str) -> None: ...

@dataclass(frozen=True)
class AppConstants:
    APP_NAME: str = 'Motivation Letter Generator'
    VERSION: str = '1.0.0'
    USER_HOME_DIR: str = os.path.expanduser('~/.jobops')
    MOTIVATIONS_DIR: str = os.path.expanduser('~/.jobops/motivations')
    WINDOW_SIZE: str = "600x200"
    ICON_SIZE: tuple = (64, 64)
    DB_NAME: str = 'jobops.db'
    CONFIG_NAME: str = 'config.json'

CONSTANTS = AppConstants()

class BaseLLMBackend(ABC):
    @abstractmethod
    def generate_response(self, prompt: str, system_prompt: Optional[str] = None) -> str: pass
    @abstractmethod
    def health_check(self) -> bool: pass

class OllamaBackend(BaseLLMBackend):
    def __init__(self, model: str = "qwen3:0.6b", base_url: str = "http://localhost:11434"):
        if not OLLAMA_AVAILABLE:
            raise ImportError("Ollama package not available")
        self.model = model
        self.base_url = base_url
        ollama.base_url = base_url
        self._logger = logging.getLogger(self.__class__.__name__)
    
    def generate_response(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        self._logger.info(f"Generating response with model: {self.model}")
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = ollama.chat(model=self.model, messages=messages)
            return response['message']['content']
        except Exception as e:
            self._logger.error(f"Ollama generation error: {e}")
            raise
    
    def health_check(self) -> bool:
        try:
            response = ollama.chat(
                model=self.model,
                messages=[{"role": "user", "content": "Hello"}]
            )
            return True
        except Exception as e:
            self._logger.error(f"Health check failed: {e}")
            return False

class OpenAIBackend(BaseLLMBackend):
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4-turbo-preview"):
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI package not available")
        
        api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OpenAI API key required")
        
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self._logger = logging.getLogger(self.__class__.__name__)
    
    def generate_response(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        self._logger.info(f"Generating response with model: {self.model}")
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=1000
            )
            return response.choices[0].message.content
        except Exception as e:
            self._logger.error(f"OpenAI generation error: {e}")
            raise
    
    def health_check(self) -> bool:
        try:
            self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10
            )
            return True
        except Exception as e:
            self._logger.error(f"Health check failed: {e}")
            return False

class GroqBackend(BaseLLMBackend):
    def __init__(self, api_key: Optional[str] = None, model: str = "mixtral-8x7b-32768"):
        if not GROQ_AVAILABLE:
            raise ImportError("Groq package not available")
        
        api_key = api_key or os.getenv('GROQ_API_KEY')
        if not api_key:
            raise ValueError("Groq API key required")
        
        self.client = Groq(api_key=api_key)
        self.model = model
        self._logger = logging.getLogger(self.__class__.__name__)
    
    def generate_response(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        self._logger.info(f"Generating response with model: {self.model}")
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=1000
            )
            return response.choices[0].message.content
        except Exception as e:
            self._logger.error(f"Groq generation error: {e}")
            raise
    
    def health_check(self) -> bool:
        try:
            self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10
            )
            return True
        except Exception as e:
            self._logger.error(f"Health check failed: {e}")
            return False

class SQLiteDocumentRepository:
    def __init__(self, db_path: str, timeout: float = 30.0):
        self.db_path = Path(db_path)
        self._logger = logging.getLogger(self.__class__.__name__)
        self.timeout = timeout
        self._init_db()
    
    def _init_db(self):
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path, timeout=self.timeout) as conn:
            c = conn.cursor()
            c.execute('PRAGMA journal_mode=WAL;')
            c.execute('''
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    filename TEXT,
                    raw_content TEXT,
                    structured_content TEXT,
                    uploaded_at TEXT,
                    reasoning_analysis TEXT
                )
            ''')
            try:
                c.execute('ALTER TABLE documents ADD COLUMN reasoning_analysis TEXT')
            except sqlite3.OperationalError:
                pass
            conn.commit()
    
    def save(self, document: Document) -> str:
        with sqlite3.connect(self.db_path, timeout=self.timeout) as conn:
            c = conn.cursor()
            c.execute(
                """INSERT OR REPLACE INTO documents 
                   (id, type, filename, raw_content, structured_content, uploaded_at, reasoning_analysis) 
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (document.id, document.type.value, document.filename,
                 document.raw_content, document.structured_content,
                 document.uploaded_at.isoformat(),
                 getattr(document, 'reasoning_analysis', None))
            )
            conn.commit()
        return document.id
    
    def get_by_id(self, doc_id: str) -> Optional[Document]:
        with sqlite3.connect(self.db_path, timeout=self.timeout) as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
            row = c.fetchone()
            
            if row:
                doc = Document(
                    id=row[0],
                    type=DocumentType(row[1]),
                    filename=row[2],
                    raw_content=row[3],
                    structured_content=row[4],
                    uploaded_at=datetime.fromisoformat(row[5])
                )
                if len(row) > 6:
                    setattr(doc, 'reasoning_analysis', row[6])
                return doc
        return None
    
    def get_by_type(self, doc_type: DocumentType) -> List[Document]:
        documents = []
        with sqlite3.connect(self.db_path, timeout=self.timeout) as conn:
            c = conn.cursor()
            c.execute(
                "SELECT * FROM documents WHERE type = ? ORDER BY uploaded_at DESC", 
                (doc_type.value,)
            )
            rows = c.fetchall()
            
            for row in rows:
                doc = Document(
                    id=row[0],
                    type=DocumentType(row[1]),
                    filename=row[2],
                    raw_content=row[3],
                    structured_content=row[4],
                    uploaded_at=datetime.fromisoformat(row[5])
                )
                if len(row) > 6:
                    setattr(doc, 'reasoning_analysis', row[6])
                documents.append(doc)
        return documents
    
    def get_latest_resume(self) -> Optional[Resume]:
        documents = self.get_by_type(DocumentType.RESUME)
        if documents:
            try:
                resume_data = json.loads(documents[0].structured_content)
                return Resume(**resume_data)
            except (json.JSONDecodeError, ValueError) as e:
                self._logger.error(f"Error parsing resume data: {e}")
                return None
        return None
    
    def delete(self, doc_id: str) -> bool:
        with sqlite3.connect(self.db_path, timeout=self.timeout) as conn:
            c = conn.cursor()
            c.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
            deleted = c.rowcount > 0
            conn.commit()
        return deleted

class Crawl4AIJobScraper:
    def __init__(self, llm_backend: LLMBackend):
        if not CRAWL4AI_AVAILABLE:
            raise ImportError("Crawl4AI package not available")
        self.llm_backend = llm_backend
        self._logger = logging.getLogger(self.__class__.__name__)
    
    def scrape_job_description(self, url: str, company: str = None, title: str = None, location: str = None) -> JobData:
        self._logger.info(f"Scraping job description from: {url}")
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                markdown_content = loop.run_until_complete(self._crawl_url(url))
            finally:
                loop.close()

            # If all fields are provided, skip LLM extraction and use them directly
            if company and title and location is not None:
                return JobData(
                    url=url,
                    title=title,
                    company=company,
                    location=location,
                    description=markdown_content[:3000],
                    requirements="",
                    company_profile_url=None,
                    company_profile=None
                )
            # Otherwise, fallback to LLM extraction as before
            system_prompt = (
                "You are an expert job posting parser. Extract the following information from the job posting markdown below and return ONLY a valid JSON object (no markdown, no code blocks, no extra text):\n"
                "{\n  'title': '...',\n  'company': '...',\n  'location': '...',\n  'company_profile_url': '...',  // If not present, suggest a likely URL such as '/about' or '/about-us', or null if unknown\n  'company_profile': '...'       // If a company profile/description is present in the markdown or at the profile URL, include it here, otherwise null\n}\n"
                "Instructions:\n"
                "- Carefully search the markdown for job title, company name, and location.\n"
                "- If the company profile or description is present, extract it. If not, suggest a likely company profile URL (e.g., '/about', '/about-us') based on the company website or job URL.\n"
                "- If you cannot find a field, use null.\n"
                "- Return ONLY the JSON object, with no extra text, markdown, or code blocks."
            )
            prompt = f"""
            Extract the following information from the job posting markdown below and return ONLY a valid JSON object (no markdown, no code blocks, no extra text):
            {{
              "title": "...",
              "company": "...",
              "location": "...",
              "company_profile_url": "...",  // If not present, suggest a likely URL such as '/about' or '/about-us', or null if unknown
              "company_profile": "..."       // If a company profile/description is present in the markdown or at the profile URL, include it here, otherwise null
            }}

            Markdown:
            {markdown_content[:10000]}
            """
            import json
            try:
                response = self.llm_backend.generate_response(prompt, system_prompt)
                cleaned_response = response.strip()
                if cleaned_response.startswith('```'):
                    cleaned_response = cleaned_response[7:]
                if cleaned_response.endswith('```'):
                    cleaned_response = cleaned_response[:-3]
                job_info = json.loads(cleaned_response.strip())
                # Use user-provided overrides if present
                title_val = title if title else job_info.get('title', '').strip() or "Unknown Position"
                company_val = company if company else job_info.get('company', '').strip() or "Unknown Company"
                location_val = location if location else job_info.get('location', '').strip() or None
                company_profile_url = job_info.get('company_profile_url', None)
                company_profile = job_info.get('company_profile', None)
            except Exception as e:
                self._logger.warning(f"LLM job field extraction failed, using fallback: {e}")
                lines = markdown_content.split('\n')
                title_val = title if title else next((line.strip('# ').strip() for line in lines if line.startswith('#')), "Unknown Position")
                company_val = company if company else "Unknown Company"
                location_val = location if location else None
                company_profile_url = None
                company_profile = None

            return JobData(
                url=url,
                title=title_val,
                company=company_val,
                location=location_val,
                description=markdown_content[:3000],
                requirements="",
                company_profile_url=company_profile_url,
                company_profile=company_profile
            )
        except Exception as e:
            self._logger.error(f"Error scraping job description: {e}")
            raise Exception(f"Failed to scrape job description: {str(e)}")
    
    async def _crawl_url(self, url: str) -> str:
        content_filter = PruningContentFilter(
            threshold=0.3,
            threshold_type="fixed",
            min_word_threshold=10
        )
        
        markdown_generator = DefaultMarkdownGenerator(
            content_filter=content_filter
        )
        
        browser_config = BrowserConfig(
            headless=True,
            java_script_enabled=True,
            verbose=False
        )
        
        crawler_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            markdown_generator=markdown_generator,
            page_timeout=30000
        )
        
        async with AsyncWebCrawler(config=browser_config) as crawler:
            result = await crawler.arun(url=url, config=crawler_config)
            
            if result and result.success:
                return result.markdown.fit_markdown or result.markdown.raw_markdown
            else:
                raise Exception(f"Failed to crawl URL: {result.error_message if result else 'Unknown error'}")
    
    def _extract_job_data_from_markdown(self, url: str, markdown_content: str) -> JobData:
        output_schema = JobData.model_json_schema()
        
        prompt = f"""
        Extract job information from the following job posting markdown and return ONLY valid JSON that matches this exact schema:

        {json.dumps(output_schema, indent=2)}

        Job posting content:
        {markdown_content[:4000]}

        Return only the JSON object with no additional text, formatting, or code blocks.
        """
        
        try:
            response = self.llm_backend.generate_response(prompt)
            
            cleaned_response = response.strip()
            if cleaned_response.startswith('```markdown'):
                cleaned_response = cleaned_response[11:]
            if cleaned_response.endswith('```'):
                cleaned_response = cleaned_response[:-3]
            
            job_info = json.loads(cleaned_response.strip())
            job_info['url'] = url
            
            return JobData(**job_info)
        except Exception as e:
            self._logger.warning(f"LLM extraction failed, using fallback: {e}")
            return self._fallback_extraction(url, markdown_content)
    
    def _fallback_extraction(self, url: str, markdown_content: str) -> JobData:
        lines = markdown_content.split('\n')
        title = next((line.strip('# ') for line in lines if line.startswith('#')), "Unknown Position")
        
        return JobData(
            url=url,
            title=title,
            company="Unknown Company",
            description=markdown_content[:1500],
            requirements=""
        )

class WebJobScraper:
    def __init__(self, llm_backend: Optional[LLMBackend] = None):
        self.llm_backend = llm_backend
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self._logger = logging.getLogger(self.__class__.__name__)
    
    def scrape_job_description(self, url: str, company: str = None, title: str = None, location: str = None) -> JobData:
        self._logger.info(f"Scraping job description from: {url}")
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            for script in soup(["script", "style"]):
                script.extract()
            
            # If all fields are provided, skip LLM extraction and use them directly
            if company and title and location is not None:
                return JobData(
                    url=url,
                    title=title,
                    company=company,
                    location=location,
                    description=self._extract_description(soup),
                    requirements=self._extract_requirements(soup)
                )
            # Otherwise, fallback to LLM extraction as before
            if self.llm_backend:
                return self._extract_with_llm(url, soup, company, title, location)
            else:
                # Use user-provided overrides if present
                title_val = title if title else self._extract_title(soup)
                company_val = company if company else self._extract_company(soup)
                location_val = location if location else None
                return JobData(
                    url=url,
                    title=title_val,
                    company=company_val,
                    location=location_val,
                    description=self._extract_description(soup),
                    requirements=self._extract_requirements(soup)
                )
            
        except Exception as e:
            self._logger.error(f"Error scraping job description: {e}")
            raise Exception(f"Failed to scrape job description: {str(e)}")
    
    def _extract_with_llm(self, url: str, soup: BeautifulSoup, company: str = None, title: str = None, location: str = None) -> JobData:
        text_content = soup.get_text(separator='\n', strip=True)
        output_schema = JobData.model_json_schema()
        
        prompt = f"""
        Extract job information from the following web page content and return ONLY valid JSON that matches this exact schema:

        {json.dumps(output_schema, indent=2)}

        Web page content:
        {text_content[:4000]}

        Return only the JSON object with no additional text, formatting, or code blocks.
        """
        
        try:
            response = self.llm_backend.generate_response(prompt)
            
            cleaned_response = response.strip()
            if cleaned_response.startswith('```'):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.endswith('```'):
                cleaned_response = cleaned_response[:-3]
            
            job_info = json.loads(cleaned_response.strip())
            job_info['url'] = url
            # Use user-provided overrides if present
            job_info['title'] = title if title else job_info.get('title', 'Unknown Position')
            job_info['company'] = company if company else job_info.get('company', 'Unknown Company')
            job_info['location'] = location if location else job_info.get('location', None)
            return JobData(**job_info)
        except Exception as e:
            self._logger.warning(f"LLM extraction failed, using fallback: {e}")
            return self._fallback_extraction(url, soup)
    
    def _fallback_extraction(self, url: str, soup: BeautifulSoup) -> JobData:
        return JobData(
            url=url,
            title=self._extract_title(soup),
            company=self._extract_company(soup),
            description=self._extract_description(soup),
            requirements=self._extract_requirements(soup)
        )
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        selectors = [
            'h1', '.job-title', '.position-title',
            '[data-testid="job-title"]', '.jobsearch-JobTitle'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)
        
        title_tag = soup.find('title')
        return title_tag.get_text(strip=True) if title_tag else "Unknown Position"
    
    def _extract_company(self, soup: BeautifulSoup) -> str:
        selectors = [
            '.company-name', '.employer-name',
            '[data-testid="company-name"]', '.jobsearch-InlineCompanyName'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)
        
        return "Unknown Company"
    
    def _extract_description(self, soup: BeautifulSoup) -> str:
        selectors = [
            '.job-description', '.jobsearch-jobDescriptionText',
            '.jobs-description', '[data-testid="job-description"]'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(separator='\n', strip=True)
        
        main_content = soup.find('main') or soup.find('body')
        if main_content:
            return main_content.get_text(separator='\n', strip=True)[:3000]
        
        return "Could not extract job description"
    
    def _extract_requirements(self, soup: BeautifulSoup) -> str:
        keywords = ['requirements', 'qualifications', 'skills', 'experience']
        
        for keyword in keywords:
            elements = soup.find_all(text=lambda text: text and keyword.lower() in text.lower())
            for element in elements:
                parent = element.parent
                if parent:
                    req_text = parent.get_text(separator='\n', strip=True)
                    if len(req_text) > 50:
                        return req_text[:1000]
        
        return ""

class ConcreteLetterGenerator:
    def __init__(self, llm_backend: LLMBackend):
        self.backend = llm_backend
        self._logger = logging.getLogger(self.__class__.__name__)
    
    def generate(self, job_data: JobData, resume: Resume, language: str = "en") -> MotivationLetter:
        self._logger.info("Generating motivation letter")
        
        system_prompt = self._create_system_prompt(job_data.company, language)
        user_prompt = self._create_user_prompt(job_data, resume, language)
        
        try:
            content = self.backend.generate_response(user_prompt, system_prompt)
            return MotivationLetter(
                job_data=job_data,
                resume=resume,
                content=content,
                language=language
            )
        except Exception as e:
            self._logger.error(f"Error generating motivation letter: {e}")
            raise Exception(f"Failed to generate motivation letter: {str(e)}")
    
    def _create_system_prompt(self, company: str, language: str) -> str:
        if language == "nl":
            return f"""Je bent een professionele HR consultant. Schrijf een overtuigende motivatiebrief gericht aan het bedrijf '{company}'.\n- Gebruik altijd een aanhef als 'Geachte {company} team' of 'Geachte Hiring Manager bij {company}'.\n- Vermijd taal die gericht is op recruiters of bureaus; richt je uitsluitend tot het bedrijf.\n- Gebruik concrete voorbeelden en motiveer waarom de kandidaat specifiek bij dit bedrijf wil werken.\n- Houd de brief tussen 300-400 woorden."""
        else:
            return f"""You are a professional HR consultant. Write a compelling motivation letter addressed directly to the company '{company}'.\n- Always use a salutation such as 'Dear {company} team' or 'Dear Hiring Manager at {company}'.\n- Avoid any recruiter or agency language; address only the company.\n- Use concrete examples and show why the candidate specifically wants to work for this company.\n- Keep the letter between 300-400 words."""
    
    def _create_user_prompt(self, job_data: JobData, resume: Resume, language: str) -> str:
        resume_summary = self._format_resume_for_prompt(resume)
        salutation_en = f"Dear {job_data.company} team," if job_data.company else "Dear Hiring Manager,"
        salutation_nl = f"Geachte {job_data.company} team," if job_data.company else "Geachte Hiring Manager,"
        if language == "nl":
            return f"""Schrijf een motivatiebrief voor:

{salutation_nl}

FUNCTIE:
Titel: {job_data.title}
Bedrijf: {job_data.company}
Beschrijving: {job_data.description}
Vereisten: {job_data.requirements}

CV SAMENVATTING:
{resume_summary}

Maak een persoonlijke en overtuigende brief, gericht aan het bedrijf zelf."""
        else:
            return f"""Write a motivation letter for:

{salutation_en}

POSITION:
Title: {job_data.title}
Company: {job_data.company}
Description: {job_data.description}
Requirements: {job_data.requirements}

RESUME SUMMARY:
{resume_summary}

Create a personal and compelling letter, addressed directly to the company."""
    
    def _format_resume_for_prompt(self, resume: Resume) -> str:
        parts = [
            f"Name: {resume.personal_info.name or 'N/A'}",
            f"Title: {resume.personal_info.title or 'N/A'}",
            f"Experience: {resume.personal_info.experience_years or 'N/A'}",
            f"Summary: {resume.summary or 'N/A'}",
        ]
        
        if resume.work_experience:
            parts.append("Recent Experience:")
            for exp in resume.work_experience[:3]:
                parts.append(f"- {exp.position or 'N/A'} at {exp.company or 'N/A'} ({exp.period or 'N/A'})")
        
        if resume.technical_skills:
            parts.append(f"Technical Skills: {', '.join(resume.technical_skills[:8])}")
        
        if resume.education:
            parts.append("Education:")
            for edu in resume.education[:2]:
                parts.append(f"- {edu.degree or 'N/A'} from {edu.institution or 'N/A'}")
        
        return '\n'.join(parts)

class DocumentExtractor:
    def __init__(self, llm_backend: LLMBackend):
        self.llm_backend = llm_backend
        self._logger = logging.getLogger(self.__class__.__name__)
    
    def extract_resume(self, raw_content: str) -> Resume:
        # Use LLM to clean and format the resume text, not to parse JSON
        system_prompt = "You are an expert resume editor. Clean up the following resume text: fix any formatting, syntax, or logical issues, and present the information in a clear, well-structured way. Do not add or remove information, just improve the clarity and flow. Return only the improved resume text."
        prompt = f"""
        Clean up and format the following resume text for clarity and logical flow. Do not add or remove information, just improve the structure and readability.

        Resume content:
        {raw_content[:6000]}
        """
        try:
            cleaned_text = self.llm_backend.generate_response(prompt, system_prompt).strip()
            return Resume(
                summary=cleaned_text,
                work_experience=[],
                education=[],
                technical_skills=[],
                soft_skills=[],
                projects=[],
                certifications=[],
                languages=[]
            )
        except Exception as e:
            self._logger.error(f"Resume cleaning failed: {e}")
            return self._create_fallback_resume(raw_content)
    
    def extract_generic_document(self, raw_content: str, doc_type: DocumentType) -> GenericDocument:
        output_schema = GenericDocument.model_json_schema()
        
        system_prompt = f"""You are an expert document parser. Extract information from {doc_type.value} documents and return structured JSON data."""
        
        prompt = f"""
        Extract and structure the document information from the following {doc_type.value} content and return ONLY valid JSON that matches this exact schema:

        {json.dumps(output_schema, indent=2)}

        Document content:
        {raw_content[:10000]}

        Instructions:
        - Extract all relevant information accurately
        - Identify key sections and content types
        - Use null for missing fields
        - Return only the JSON object with no additional text, formatting, or code blocks
        """
        
        try:
            response = self.llm_backend.generate_response(prompt, system_prompt)
            
            cleaned_response = response.strip()
            if cleaned_response.startswith('```markdown'):
                cleaned_response = cleaned_response[14:]
            if cleaned_response.endswith('```'):
                cleaned_response = cleaned_response[:-3]
            
            doc_data = json.loads(cleaned_response.strip())
            return GenericDocument(**doc_data)
            
        except Exception as e:
            self._logger.error(f"Document extraction failed: {e}")
            return self._create_fallback_document(raw_content, doc_type)
    
    def _create_fallback_resume(self, raw_content: str) -> Resume:
        lines = raw_content.split('\n')
        name = next((line.strip() for line in lines[:5] if line.strip() and not '@' in line), "Unknown")
        
        return Resume(
            personal_info=PersonalInfo(name=name),
            summary=raw_content[:500],
            work_experience=[],
            education=[],
            technical_skills=[],
            soft_skills=[],
            projects=[],
            certifications=[],
            languages=[]
        )
    
    def _create_fallback_document(self, raw_content: str, doc_type: DocumentType) -> GenericDocument:
        lines = raw_content.split('\n')
        title = next((line.strip() for line in lines[:3] if line.strip()), "Untitled Document")
        
        return GenericDocument(
            content_type=doc_type.value,
            title=title,
            key_points=[],
            sections={},
            metadata={}
        )

class LLMBackendFactory:
    @staticmethod
    def create(backend_type: str, settings: Dict[str, Any]) -> LLMBackend:
        if backend_type == "ollama":
            return OllamaBackend(
                model=settings.get('model', 'qwen3:0.6b'),
                base_url=settings.get('base_url', 'http://localhost:11434')
            )
        elif backend_type == "openai":
            return OpenAIBackend(
                model=settings.get('model', 'gpt-4-turbo-preview')
            )
        elif backend_type == "groq":
            return GroqBackend(
                model=settings.get('model', 'mixtral-8x7b-32768')
            )
        else:
            raise ValueError(f"Unsupported backend type: {backend_type}")

class JSONConfigManager:
    def __init__(self, config_path: str):
        self.config_path = Path(config_path)
        self._logger = logging.getLogger(self.__class__.__name__)
    
    def load(self) -> AppConfig:
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    config_data = json.load(f)
                return AppConfig(**config_data)
            else:
                config = AppConfig()
                self.save(config)
                return config
        except Exception as e:
            self._logger.warning(f"Error loading config: {e}, using defaults")
            return AppConfig()
    
    def save(self, config: AppConfig) -> None:
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(config.dict(), f, indent=2)
        except Exception as e:
            self._logger.error(f"Error saving config: {e}")

class SystemNotificationService:
    def __init__(self, app_name: str = "JobOps"):
        self.app_name = app_name
        self._logger = logging.getLogger(self.__class__.__name__)
    
    def notify(self, title: str, message: str) -> None:
        self._logger.info(f"Notification: {title} - {message}")
        try:
            notification.notify(
                title=title,
                message=message,
                app_name=self.app_name,
                timeout=3
            )
        except Exception as e:
            self._logger.warning(f"Notification failed: {e}")

class JobOpsApplication:
    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = Path(base_dir or CONSTANTS.USER_HOME_DIR)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        self._setup_logging()
        self._logger = logging.getLogger(self.__class__.__name__)
        
        config_path = self.base_dir / CONSTANTS.CONFIG_NAME
        self.config_manager = JSONConfigManager(str(config_path))
        self.config = self.config_manager.load()
        
        self._initialize_services()
    
    def _setup_logging(self):
        log_file = self.base_dir / 'app.log'
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
    
    def _initialize_services(self):
        db_path = self.base_dir / CONSTANTS.DB_NAME
        # Use sqlite_timeout from config if present
        timeout = self.config.sqlite_timeout if hasattr(self.config, 'sqlite_timeout') else 30.0
        self.repository = SQLiteDocumentRepository(str(db_path), timeout=timeout)
        
        backend_settings = self.config.backend_settings[self.config.backend]
        self.llm_backend = LLMBackendFactory.create(self.config.backend, backend_settings)

        # Ensure Playwright browsers are installed if using Crawl4AI
        if CRAWL4AI_AVAILABLE:
            try:
                from playwright.sync_api import sync_playwright
                import shutil
                # Check if chromium executable exists
                chromium_path = os.path.expanduser(r"~/.cache/ms-playwright/chromium-*/chrome-*/chrome.exe")
                # This is a rough check; Playwright's API is more robust
                # Try launching a browser to see if it works
                with sync_playwright() as p:
                    try:
                        browser = p.chromium.launch(headless=True)
                        browser.close()
                    except Exception:
                        logging.info("Playwright browsers not found. Installing browsers, this may take a few minutes...")
                        try:
                            self.notification_service.notify(
                                "JobOps",
                                "Installing Playwright browsers. This may take a few minutes on first run."
                            )
                        except Exception:
                            pass
                        import subprocess
                        subprocess.run(["playwright", "install"], check=True)
            except ImportError:
                pass
            except Exception as e:
                logging.warning(f"Could not verify or install Playwright browsers: {e}")
            self.job_scraper = Crawl4AIJobScraper(self.llm_backend)
        else:
            self.job_scraper = WebJobScraper(self.llm_backend)
        
        self.letter_generator = ConcreteLetterGenerator(self.llm_backend)
        self.notification_service = SystemNotificationService()
        self.document_extractor = DocumentExtractor(self.llm_backend)

        # Prompt for personal info if missing
        if not self.config.app_settings.get('personal_info'):
            import tkinter as tk
            from tkinter import simpledialog
            root = tk.Tk()
            root.withdraw()
            name = simpledialog.askstring("Personal Info", "Enter your full name:")
            phone = simpledialog.askstring("Personal Info", "Enter your phone number:")
            email = simpledialog.askstring("Personal Info", "Enter your email address:")
            city = simpledialog.askstring("Personal Info", "Enter your city:")
            linkedin = simpledialog.askstring("Personal Info", "Enter your LinkedIn URL:")
            root.destroy()
            self.config.app_settings['personal_info'] = {
                'name': name or '',
                'phone': phone or '',
                'email': email or '',
                'city': city or '',
                'linkedin': linkedin or ''
            }
            self.config_manager.save(self.config)
    
    def generate_motivation_letter(self, job_url: str, language: str = "en", company: str = None, title: str = None, location: str = None) -> str:
        try:
            job_data = self.job_scraper.scrape_job_description(
                job_url,
                company=company,
                title=title,
                location=location
            )

            # Aggregate all relevant documents (resume, certificate, etc.)
            doc_types = [DocumentType.RESUME, DocumentType.CERTIFICATION]
            all_docs = []
            for dt in doc_types:
                all_docs.extend(self.repository.get_by_type(dt))
            # Sort by upload date (latest last)
            all_docs.sort(key=lambda d: d.uploaded_at)
            # Concatenate all structured_content
            combined_docs_markdown = "\n\n".join([doc.structured_content for doc in all_docs if doc.structured_content])

            # Fetch all previous generated motivation letters (COVER_LETTER)
            previous_letters = self.repository.get_by_type(DocumentType.COVER_LETTER)
            previous_letters.sort(key=lambda d: d.uploaded_at)
            previous_letters_markdown = "\n\n".join([doc.structured_content for doc in previous_letters if doc.structured_content])

            if not combined_docs_markdown.strip():
                raise ValueError("No resume or relevant documents found. Please upload a resume or certificate first.")

            # Add personal info to the context
            personal_info = self.config.app_settings.get('personal_info', {})
            personal_info_md = f"""
**Name:** {personal_info.get('name', '')}
**Phone:** {personal_info.get('phone', '')}
**Email:** {personal_info.get('email', '')}
**City:** {personal_info.get('city', '')}
**LinkedIn:** {personal_info.get('linkedin', '')}
"""
            full_resume_md = personal_info_md + "\n\n" + combined_docs_markdown

            # Use the combined markdown as the resume summary
            resume = Resume(summary=full_resume_md)

            # Enhance prompt with previous letters if any
            if previous_letters_markdown.strip():
                # Optionally, you can prepend or append this to the resume summary or add as extra context
                resume.summary += "\n\n# Previous Motivation Letters\n" + previous_letters_markdown

            letter = self.letter_generator.generate(job_data, resume, language)

            # Save the generated letter as a Document in the database
            import re
            # Extract <think>...</think> block if present
            llm_response = letter.content
            think_match = re.search(r'<think>(.*?)</think>', llm_response, re.DOTALL | re.IGNORECASE)
            reasoning_analysis = think_match.group(1).strip() if think_match else None
            # Remove <think>...</think> from the content for structured_content
            structured_content = re.sub(r'<think>.*?</think>', '', llm_response, flags=re.DOTALL | re.IGNORECASE).strip()
            # Set filename as '{Full Name} Cover Letter'
            full_name = personal_info.get('name', '').strip() or ''
            filename = f"{full_name} Cover Letter".strip() if full_name else "Cover Letter"
            document = Document(
                type=DocumentType.COVER_LETTER,
                filename=filename,
                raw_content=letter.content,
                structured_content=structured_content,
                reasoning_analysis=reasoning_analysis
            )
            self.repository.save(document)

            self.notification_service.notify(
                "JobOps", 
                f"Motivation letter generated and stored in database."
            )

            return f"Motivation letter generated and stored in database with ID: {document.id}"

        except Exception as e:
            self._logger.error(f"Error generating motivation letter: {e}")
            self.notification_service.notify("JobOps Error", str(e))
            raise
    
    def upload_document(self, file_path: str, doc_type: DocumentType) -> Document:
        try:
            file_path = Path(file_path)
            
            if file_path.suffix.lower() == '.pdf' and PDF_AVAILABLE:
                with pdfplumber.open(file_path) as pdf:
                    raw_content = "\n".join(page.extract_text() or '' for page in pdf.pages)
            else:
                with open(file_path, 'r', encoding='utf-8') as f:
                    raw_content = f.read()

            # Use LLM to clean up and restructure content into markdown
            system_prompt = "You are an expert document formatter. Clean up and restructure the following document content into clear, well-formatted markdown. Do not add or remove information, just improve the structure and readability. Return only the improved markdown. Optionally, you may include a <think>...</think> block with your reasoning before the markdown code block."
            prompt = f"""
            Clean up and format the following document content as markdown for clarity and logical flow. Do not add or remove information, just improve the structure and readability.

            Document content:
            {raw_content[:6000]}
            """
            try:
                llm_response = self.llm_backend.generate_response(prompt, system_prompt).strip()
                import re
                # Extract <think>...</think>
                reasoning_analysis = None
                think_match = re.search(r'<think>(.*?)</think>', llm_response, re.DOTALL | re.IGNORECASE)
                if think_match:
                    reasoning_analysis = think_match.group(1).strip()
                # Extract markdown code block
                md_match = re.search(r'```markdown\s*(.*?)\s*```', llm_response, re.DOTALL | re.IGNORECASE)
                if md_match:
                    structured_content = md_match.group(1).strip()
                else:
                    # Remove <think>...</think> if present
                    structured_content = re.sub(r'<think>.*?</think>', '', llm_response, flags=re.DOTALL | re.IGNORECASE).strip()
            except Exception as e:
                self._logger.error(f"Document markdown cleaning failed: {e}")
                structured_content = raw_content
                reasoning_analysis = None

            document = Document(
                type=doc_type,
                filename=file_path.name,
                raw_content=raw_content,
                structured_content=structured_content,
                reasoning_analysis=reasoning_analysis
            )
            
            self.repository.save(document)
            
            self.notification_service.notify(
                "JobOps", 
                f"Document uploaded: {document.filename}"
            )
            
            return document
            
        except Exception as e:
            self._logger.error(f"Error uploading document: {e}")
            self.notification_service.notify("JobOps Error", str(e))
            raise
    
    def run(self):
        self._logger.info(f"Starting {CONSTANTS.APP_NAME} v{CONSTANTS.VERSION}")

        def create_image():
            img = Image.new('RGB', CONSTANTS.ICON_SIZE, color=(70, 130, 180))
            d = ImageDraw.Draw(img)
            d.rectangle([16, 16, 48, 48], fill=(255, 255, 255))
            d.text((22, 22), "J", fill=(70, 130, 180))
            return img

        def on_upload_resume(icon, item):
            import tkinter as tk
            from tkinter import filedialog, messagebox
            import threading
            import time

            # Animation images
            def create_image(color):
                img = Image.new('RGB', CONSTANTS.ICON_SIZE, color=color)
                d = ImageDraw.Draw(img)
                d.rectangle([16, 16, 48, 48], fill=(255, 255, 255))
                d.text((22, 22), "J", fill=color)
                return img
            img1 = create_image((70, 130, 180))
            img2 = create_image((180, 130, 70))

            animating = True
            def animate_icon():
                flip = False
                while animating:
                    icon.icon = img1 if flip else img2
                    flip = not flip
                    time.sleep(0.3)
                icon.icon = img1  # restore original

            def do_upload(file_path):
                nonlocal animating
                anim_thread = threading.Thread(target=animate_icon, daemon=True)
                animating = True
                anim_thread.start()
                try:
                    doc = self.upload_document(file_path, DocumentType.RESUME)
                    root.after(0, lambda: messagebox.showinfo("Success", f"Resume uploaded: {doc.filename}"))
                except Exception as e:
                    root.after(0, lambda e=e: messagebox.showerror("Error", f"Error uploading resume: {e}"))
                finally:
                    animating = False
                    root.after(0, root.destroy)

            def ask_and_upload():
                file_path = filedialog.askopenfilename(title="Select Resume File", filetypes=[("PDF or Text Files", "*.pdf *.txt")])
                if file_path:
                    threading.Thread(target=do_upload, args=(file_path,), daemon=True).start()
                else:
                    root.destroy()

            root = tk.Tk()
            root.withdraw()
            root.after(0, ask_and_upload)
            root.mainloop()

        def on_generate_letter(icon, item):
            import tkinter as tk
            from tkinter import messagebox
            import threading
            import time

            # Animation images
            def create_image(color):
                img = Image.new('RGB', CONSTANTS.ICON_SIZE, color=color)
                d = ImageDraw.Draw(img)
                d.rectangle([16, 16, 48, 48], fill=(255, 255, 255))
                d.text((22, 22), "J", fill=color)
                return img
            img1 = create_image((70, 130, 180))
            img2 = create_image((180, 130, 70))

            animating = True
            def animate_icon():
                flip = False
                while animating:
                    icon.icon = img1 if flip else img2
                    flip = not flip
                    time.sleep(0.3)
                icon.icon = img1  # restore original

            def do_generate(job_url, company, title, location, language):
                nonlocal animating
                anim_thread = threading.Thread(target=animate_icon, daemon=True)
                animating = True
                anim_thread.start()
                try:
                    filepath = self.generate_motivation_letter(
                        job_url, language, company=company, title=title, location=location
                    )
                    root.after(0, lambda: messagebox.showinfo("Success", f"Motivation letter generated and stored in database."))
                except Exception as e:
                    root.after(0, lambda: messagebox.showerror("Error", f"Error generating letter: {e}"))
                finally:
                    animating = False
                    root.after(0, root.destroy)

            # Wizard dialog implementation
            class Wizard(tk.Toplevel):
                def __init__(self, master):
                    super().__init__(master)
                    self.title("Generate Motivation Letter")
                    self.geometry("400x250")
                    self.resizable(False, False)
                    self.steps = [
                        {"label": "Job URL", "var": tk.StringVar()},
                        {"label": "Company Name", "var": tk.StringVar()},
                        {"label": "Job Title", "var": tk.StringVar()},
                        {"label": "Location", "var": tk.StringVar()},
                        {"label": "Language (en/nl)", "var": tk.StringVar(value="en")},
                    ]
                    self.current = 0
                    self.widgets = {}
                    self.protocol("WM_DELETE_WINDOW", self.on_cancel)
                    self.build_ui()
                    self.show_step()

                def build_ui(self):
                    self.progress = tk.Label(self, text="", font=("Arial", 10))
                    self.progress.pack(pady=(10, 0))
                    self.label = tk.Label(self, text="", font=("Arial", 12))
                    self.label.pack(pady=(20, 5))
                    self.entry = tk.Entry(self, textvariable=self.steps[0]["var"], width=40)
                    self.entry.pack(pady=(0, 10))
                    self.button_frame = tk.Frame(self)
                    self.button_frame.pack(pady=10)
                    self.back_btn = tk.Button(self.button_frame, text="Back", command=self.prev_step, state=tk.DISABLED)
                    self.back_btn.grid(row=0, column=0, padx=5)
                    self.next_btn = tk.Button(self.button_frame, text="Next", command=self.next_step)
                    self.next_btn.grid(row=0, column=1, padx=5)
                    self.submit_btn = tk.Button(self.button_frame, text="Submit", command=self.on_submit)
                    self.submit_btn.grid(row=0, column=2, padx=5)
                    self.submit_btn.config(state=tk.DISABLED)

                def show_step(self):
                    step = self.steps[self.current]
                    self.label.config(text=step["label"])
                    self.entry.config(textvariable=step["var"])
                    self.progress.config(text=f"Step {self.current+1} of {len(self.steps)}")
                    self.entry.focus_set()
                    self.back_btn.config(state=tk.NORMAL if self.current > 0 else tk.DISABLED)
                    if self.current == len(self.steps) - 1:
                        self.next_btn.config(state=tk.DISABLED)
                        self.submit_btn.config(state=tk.NORMAL)
                    else:
                        self.next_btn.config(state=tk.NORMAL)
                        self.submit_btn.config(state=tk.DISABLED)

                def next_step(self):
                    if self.current < len(self.steps) - 1:
                        self.current += 1
                        self.show_step()

                def prev_step(self):
                    if self.current > 0:
                        self.current -= 1
                        self.show_step()

                def on_submit(self):
                    values = [step["var"].get().strip() for step in self.steps]
                    job_url, company, title, location, language = values
                    self.destroy()
                    threading.Thread(
                        target=do_generate,
                        args=(job_url, company, title, location, language),
                        daemon=True
                    ).start()

                def on_cancel(self):
                    self.destroy()

            root = tk.Tk()
            root.withdraw()
            wizard = Wizard(root)
            root.mainloop()

        def on_exit(icon, item):
            icon.stop()
            print("Exiting application. Goodbye!")
            try:
                self.notification_service.notify("JobOps", "Exiting application. Goodbye!")
                # KILL ALL THREADS
                for thread in threading.enumerate():
                    thread.join()
                # KILL ALL PROCESSES belongs to this application
                for process in psutil.process_iter():
                    if process.name() == "jobops.exe":
                        process.kill()
            except Exception as e:
                logging.error(f"Error notifying: {e}")
            sys.exit()
            
        def on_help_github_repo(icon, item):
            webbrowser.open("https://github.com/codesapienbe/jobops-toolbar")

        menu = pystray.Menu(
            pystray.MenuItem("Upload", on_upload_resume),
            pystray.MenuItem("Generate", on_generate_letter),
            pystray.MenuItem("Help", on_help_github_repo),
            pystray.MenuItem("Exit", on_exit)
        )
        icon = pystray.Icon(CONSTANTS.APP_NAME, create_image(), CONSTANTS.APP_NAME, menu)
        icon.run()

def main():
    try:
        app = JobOpsApplication()
        app.run()
    except KeyboardInterrupt:
        logging.info("Application interrupted by user")
    except Exception as e:
        logging.error(f"Application error: {e}")
        raise
    finally:
        logging.info("Application ended")

if __name__ == "__main__":
    main()
