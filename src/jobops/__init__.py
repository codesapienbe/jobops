#!/usr/bin/env python3

"""
AI Motivation Letter Generator

Een applicatie die automatisch motivatiebrieven genereert op basis van job descriptions
van URLs, gebruikmakend van verschillende LLM backends (OpenAI, Ollama, Groq).

Author: Mustafa Yilmaz
License: MIT
"""

import os
import json
import logging
from typing import Dict, Any
from datetime import datetime
import threading
import pystray
from PIL import Image, ImageDraw
import sqlite3

# Third-party imports
import requests
from bs4 import BeautifulSoup
from plyer import notification

# LLM Backend imports
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

# Add dotenv support
from dotenv import load_dotenv
load_dotenv()

# =============================================================================
# CONSTANTS AND CONFIGURATION
# =============================================================================

class AppConstants:
    """Application-wide constants and configuration values."""
    
    APP_NAME = 'Motivation Letter Generator'
    VERSION = '1.0.0'
    USER_HOME_DIR = os.path.expanduser('~/.jobops')
    MOTIVATIONS_DIR = os.path.expanduser('~/.jobops/motivations')
    WINDOW_SIZE = "600x200"
    ICON_SIZE = (64, 64)
    
    # Default resume data (based on provided CV)
    DEFAULT_RESUME = {
        "personal_info": {
            "name": "Mustafa Yilmaz",
            "title": "Full Stack / Java Developer",
            "experience_years": "5+",
            "location": "Belgium"
        },
        "summary": "Java developer with 5+ years in financial messaging systems, enterprise apps & AI tech. Background spans SWIFT, entrepreneurship & teaching. Currently pursuing AI/ML postgraduate studies while contributing to open-source. Strong in Java, Spring & databases, with passion for knowledge sharing.",
        "work_experience": [
            {
                "position": "Freelance Software Crafter",
                "company": "MeOwn",
                "period": "Feb 2025 - Current",
                "description": "Working as an independent software engineer developing custom solutions. Developing Python applications with computer vision and AI capabilities using FastAPI. Building backend systems with TypeScript and NestJS framework."
            },
            {
                "position": "Senior Java Developer", 
                "company": "TheMatchBox",
                "period": "Nov 2024 - Jan 2025",
                "description": "Worked on custom plugins for ElasticSearch. Contributed to TheMatchBox core product providing API for matching between Candidates and Jobs using ontology and advanced algorithms."
            },
            {
                "position": "Software Engineer",
                "company": "S.W.I.F.T",
                "period": "June 2023 - Nov 2024", 
                "description": "Working on SWIFT's messaging protocols, enhancing the efficiency and security of financial communication. Worked in Alliance Messaging Hub which has the highest revenue share in the financial market."
            },
            {
                "position": "Java/Python Trainer",
                "company": "INTEC BRUSSEL",
                "period": "Jan 2020 - June 2023",
                "description": "Worked as a Java/Python Trainer teaching Java EE, Python, and shell. Students work at prestigious institutions like KU Leuven and FOD. Attended a hackathon in Belgium and won the 3rd prize."
            }
        ],
        "education": [
            {
                "degree": "Postgraduate AI",
                "institution": "Erasmus Hogeschool Brussel",
                "period": "2024-2025 (Ongoing)",
                "description": "Artificial Intelligence, Machine Learning, Deep Learning, Natural Language Processing, and MLOps"
            }
        ],
        "technical_skills": [
            "Java (Spring Boot, JPA, JDK 11+)",
            "Python (Pandas, Transformers, OpenCV)",
            "Databases (MySQL, PostgreSQL, MongoDB)",
            "Messaging (IBM-MQ, RabbitMQ, ZeroMQ)",
            "API Development (REST, Spring Boot, Flask)",
            "Frontend (TypeScript, React)",
            "DevOps (Docker, Kubernetes, CI/CD)",
            "Version Control (Git, GitHub, GitLab)"
        ],
        "certifications": [
            "Agile in Software Development",
            "SWIFT Messaging Systems", 
            "Best Security Practices in Software Companies"
        ],
        "languages": ["English", "Turkish", "Dutch"],
        "open_source": "I actively work on open-source projects and dedicate time on a daily basis to contribute to the community. My GitHub profile showcases several projects including contributions to cybersecurity toolkits and AI-related repositories."
    }

# =============================================================================
# DATABASE SETUP
# =============================================================================

def get_db_path():
    return os.path.expanduser('~/.jobops/jobops.db')

def init_db():
    db_path = get_db_path()
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
            filename TEXT,
            raw_content TEXT,
            structured_content TEXT,
            uploaded_at TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Enum for document types
class DocumentType:
    RESUME = 'resume'
    COVER_LETTER = 'cover_letter'
    JOB_DESCRIPTION = 'job_description'
    REFERENCE_LETTER = 'reference_letter'
    OTHER = 'other'
    ALL = [RESUME, COVER_LETTER, JOB_DESCRIPTION, REFERENCE_LETTER, OTHER]

init_db()

# =============================================================================
# LOGGING SETUP
# =============================================================================

def setup_logging():
    """Initialize logging configuration."""
    os.makedirs(os.path.dirname(AppConstants.MOTIVATIONS_DIR), exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler(os.path.join(AppConstants.USER_HOME_DIR, 'app.log'), encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

def log(msg: str, level: str = 'info'):
    """Log a message with specified level."""
    getattr(logging, level)(msg)

setup_logging()

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def show_notification(title: str, message: str):
    """Show system notification."""
    log(f"Notification: {title} - {message}")
    try:
        notification.notify(
            title=title,
            message=message,
            app_name=AppConstants.APP_NAME,
            timeout=3
        )
    except Exception as e:
        log(f"Notification error: {e}", 'warning')

def initialize_directories():
    """Create necessary directories."""
    os.makedirs(AppConstants.USER_HOME_DIR, exist_ok=True)
    os.makedirs(AppConstants.MOTIVATIONS_DIR, exist_ok=True)

# =============================================================================
# JOB SCRAPER
# =============================================================================

class JobScraper:
    """Scrapes job descriptions from URLs."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def scrape_job_description(self, url: str) -> Dict[str, str]:
        """Scrape job description from URL."""
        try:
            log(f"Scraping job description from: {url}")
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.extract()
            
            # Extract title
            title = self._extract_title(soup)
            
            # Extract company
            company = self._extract_company(soup)
            
            # Extract job description
            description = self._extract_description(soup)
            
            # Extract requirements if available
            requirements = self._extract_requirements(soup)
            
            return {
                'url': url,
                'title': title,
                'company': company,
                'description': description,
                'requirements': requirements,
                'scraped_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            log(f"Error scraping job description: {e}", 'error')
            raise Exception(f"Failed to scrape job description: {str(e)}")
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract job title from HTML."""
        # Try multiple selectors for job title
        selectors = [
            'h1',
            '.job-title',
            '.position-title',
            '[data-testid="job-title"]',
            '.jobsearch-JobTitle',
            '.jobs-unified-top-card__job-title'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)
        
        # Fallback to page title
        title_tag = soup.find('title')
        return title_tag.get_text(strip=True) if title_tag else "Unknown Position"
    
    def _extract_company(self, soup: BeautifulSoup) -> str:
        """Extract company name from HTML."""
        selectors = [
            '.company-name',
            '.employer-name',
            '[data-testid="company-name"]',
            '.jobsearch-InlineCompanyName',
            '.jobs-unified-top-card__company-name'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)
        
        return "Unknown Company"
    
    def _extract_description(self, soup: BeautifulSoup) -> str:
        """Extract job description from HTML."""
        # Try to find job description container
        selectors = [
            '.job-description',
            '.jobsearch-jobDescriptionText',
            '.jobs-description',
            '[data-testid="job-description"]',
            '.description',
            '.job-details'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(separator='\n', strip=True)
        
        # Fallback: get main content area
        main_content = soup.find('main') or soup.find('body')
        if main_content:
            return main_content.get_text(separator='\n', strip=True)[:3000]  # Limit length
        
        return "Could not extract job description"
    
    def _extract_requirements(self, soup: BeautifulSoup) -> str:
        """Extract job requirements from HTML."""
        requirements_keywords = ['requirements', 'qualifications', 'skills', 'experience']
        
        for keyword in requirements_keywords:
            # Look for sections containing requirements
            elements = soup.find_all(text=lambda text: text and keyword.lower() in text.lower())
            for element in elements:
                parent = element.parent
                if parent:
                    # Get the next sibling or parent content
                    req_text = parent.get_text(separator='\n', strip=True)
                    if len(req_text) > 50:  # Only if substantial content
                        return req_text[:1000]  # Limit length
        
        return ""

# =============================================================================
# LLM BACKENDS
# =============================================================================

class LLMBackend:
    """Base class for LLM backends."""
    
    def generate_response(self, prompt: str, system_prompt: str = None) -> str:
        """Generate response from the LLM."""
        raise NotImplementedError("Subclasses must implement generate_response")

class OllamaBackend(LLMBackend):
    """Ollama backend for local LLM inference."""
    
    def __init__(self, model: str = "llama2", base_url: str = "http://localhost:11434"):
        if not OLLAMA_AVAILABLE:
            raise ImportError("Ollama package not installed. Install with: pip install ollama")
        self.model = model
        self.base_url = base_url
        ollama.base_url = base_url
    
    def generate_response(self, prompt: str, system_prompt: str = None) -> str:
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = ollama.chat(model=self.model, messages=messages)
            return response['message']['content']
        except Exception as e:
            log(f"Ollama generation error: {e}", 'error')
            raise

class OpenAIBackend(LLMBackend):
    """OpenAI API backend."""
    
    def __init__(self, api_key: str = None, model: str = "gpt-4-turbo-preview"):
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI package not installed. Install with: pip install openai")
        if not api_key:
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                raise ValueError("OpenAI API key not provided and not found in environment")
        self.client = OpenAI(api_key=api_key)
        self.model = model
    
    def generate_response(self, prompt: str, system_prompt: str = None) -> str:
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
            log(f"OpenAI generation error: {e}", 'error')
            raise

class GroqBackend(LLMBackend):
    """Groq API backend."""
    
    def __init__(self, api_key: str = None, model: str = "mixtral-8x7b-32768"):
        if not GROQ_AVAILABLE:
            raise ImportError("Groq package not installed. Install with: pip install groq")
        if not api_key:
            api_key = os.getenv('GROQ_API_KEY')
            if not api_key:
                raise ValueError("Groq API key not provided and not found in environment")
        self.client = Groq(api_key=api_key)
        self.model = model
    
    def generate_response(self, prompt: str, system_prompt: str = None) -> str:
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
            log(f"Groq generation error: {e}", 'error')
            raise

# =============================================================================
# MOTIVATION LETTER GENERATOR
# =============================================================================

class MotivationLetterGenerator:
    """Generates motivation letters using LLM backends."""
    
    def __init__(self, backend: LLMBackend):
        self.backend = backend
    
    def generate_letter(self, job_data: Dict[str, str], resume_data: Dict[str, Any], language: str = "en") -> str:
        """Generate motivation letter based on job and resume data."""
        
        # Create system prompt
        system_prompt = self._create_system_prompt(language)
        
        # Create user prompt
        user_prompt = self._create_user_prompt(job_data, resume_data, language)
        
        try:
            log("Generating motivation letter with AI...")
            response = self.backend.generate_response(user_prompt, system_prompt)
            log("Motivation letter generated successfully")
            return response
        except Exception as e:
            log(f"Error generating motivation letter: {e}", 'error')
            raise Exception(f"Failed to generate motivation letter: {str(e)}")
    
    def _create_system_prompt(self, language: str) -> str:
        """Create system prompt for the LLM."""
        if language == "nl":
            return """Je bent een professionele HR consultant en expert in het schrijven van motivatiebrieven. 
Je taak is om een overtuigende, gepersonaliseerde motivatiebrief te schrijven die:

1. De kandidaat perfect matcht met de functie
2. Concrete voorbeelden uit de ervaring benadrukt
3. Toont waarom de kandidaat specifiek bij dit bedrijf wil werken
4. Een professionele maar warme toon heeft
5. Relevant is voor de Nederlandse/Belgische arbeidsmarkt

Structuur de brief met:
- Gepersonaliseerde opening
- 2-3 paragrafen die relevante ervaring benadrukken
- Specifieke motivatie voor het bedrijf/functie
- Sterke, professionele afsluiting

Schrijf in perfect Nederlands (België) en houd de brief tussen 300-400 woorden."""

        else:  # English
            return """You are a professional HR consultant and expert in writing compelling motivation letters.
Your task is to write a persuasive, personalized motivation letter that:

1. Perfectly matches the candidate to the position
2. Highlights concrete examples from experience
3. Shows why the candidate specifically wants to work for this company
4. Has a professional yet warm tone
5. Is relevant for the European job market

Structure the letter with:
- Personalized opening
- 2-3 paragraphs highlighting relevant experience
- Specific motivation for the company/position
- Strong, professional closing

Write in perfect English and keep the letter between 300-400 words."""
    
    def _create_user_prompt(self, job_data: Dict[str, str], resume_data: Dict[str, Any], language: str) -> str:
        """Create user prompt with job and resume data."""
        
        # Format resume data
        resume_summary = self._format_resume_for_prompt(resume_data)
        
        if language == "nl":
            prompt = f"""Schrijf een motivatiebrief voor de volgende functie:

FUNCTIE INFORMATIE:
Titel: {job_data.get('title', 'Onbekend')}
Bedrijf: {job_data.get('company', 'Onbekend')}
URL: {job_data.get('url', '')}

FUNCTIEOMSCHRIJVING:
{job_data.get('description', '')}

VEREISTEN:
{job_data.get('requirements', '')}

KANDIDAAT CV SAMENVATTING:
{resume_summary}

Schrijf een motivatiebrief die specifiek ingaat op deze functie en toont hoe de kandidaat ervaring perfect aansluit bij de vereisten. Gebruik concrete voorbeelden en toon echte interesse in het bedrijf."""

        else:  # English
            prompt = f"""Write a motivation letter for the following position:

JOB INFORMATION:
Title: {job_data.get('title', 'Unknown')}
Company: {job_data.get('company', 'Unknown')}
URL: {job_data.get('url', '')}

JOB DESCRIPTION:
{job_data.get('description', '')}

REQUIREMENTS:
{job_data.get('requirements', '')}

CANDIDATE CV SUMMARY:
{resume_summary}

Write a motivation letter that specifically addresses this position and shows how the candidate's experience perfectly aligns with the requirements. Use concrete examples and show genuine interest in the company."""
        
        return prompt
    
    def _format_resume_for_prompt(self, resume_data: Dict[str, Any]) -> str:
        """Format resume data for the prompt."""
        summary = []
        
        # Personal info
        personal = resume_data.get('personal_info', {})
        summary.append(f"Name: {personal.get('name', '')}")
        summary.append(f"Title: {personal.get('title', '')}")
        summary.append(f"Experience: {personal.get('experience_years', '')} years")
        
        # Professional summary
        if resume_data.get('summary'):
            summary.append(f"\nSummary: {resume_data['summary']}")
        
        # Work experience
        work_exp = resume_data.get('work_experience', [])
        if work_exp:
            summary.append("\nWork Experience:")
            for i, exp in enumerate(work_exp[:3]):  # Top 3 most recent
                summary.append(f"- {exp.get('position', '')} at {exp.get('company', '')} ({exp.get('period', '')})")
                summary.append(f"  {exp.get('description', '')}")
        
        # Technical skills
        skills = resume_data.get('technical_skills', [])
        if skills:
            summary.append(f"\nTechnical Skills: {', '.join(skills[:10])}")  # Top 10 skills
        
        # Education
        education = resume_data.get('education', [])
        if education:
            summary.append("\nEducation:")
            for edu in education:
                summary.append(f"- {edu.get('degree', '')} at {edu.get('institution', '')} ({edu.get('period', '')})")
        
        # Certifications
        certs = resume_data.get('certifications', [])
        if certs:
            summary.append(f"\nCertifications: {', '.join(certs)}")
        
        return '\n'.join(summary)

# =============================================================================
# MAIN APPLICATION GUI
# =============================================================================

class MotivationLetterApp:
    """Main application class."""
    
    def __init__(self):
        import tkinter as tk
        initialize_directories()
        self.job_scraper = JobScraper()
        self.config = self._load_config()
        self.backend = self._initialize_backend()
        self.root = tk.Tk()
        self.root.withdraw()  # Hide the main window
        self._setup_hotkey_listener()

    def _load_config(self) -> Dict[str, Any]:
        """Load or create configuration file."""
        config_path = os.path.join(AppConstants.USER_HOME_DIR, 'config.json')
        default_config = {
            'backend': 'ollama',  # ollama, openai, or groq
            'backend_settings': {
                'ollama': {
                    'model': 'llama2',
                    'base_url': 'http://localhost:11434'
                },
                'openai': {
                    'model': 'gpt-4-turbo-preview'
                },
                'groq': {
                    'model': 'mixtral-8x7b-32768'
                }
            }
        }
        
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    return json.load(f)
            else:
                with open(config_path, 'w') as f:
                    json.dump(default_config, f, indent=2)
                return default_config
        except Exception as e:
            log(f"Error loading config, using defaults: {e}", 'warning')
            return default_config
    
    def _save_config(self):
        """Save current configuration."""
        config_path = os.path.join(AppConstants.USER_HOME_DIR, 'config.json')
        try:
            with open(config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            log(f"Error saving config: {e}", 'error')
    
    def _initialize_backend(self) -> LLMBackend:
        """Initialize the selected backend."""
        backend_type = self.config['backend']
        settings = self.config['backend_settings'][backend_type]
        
        try:
            if backend_type == 'ollama':
                return OllamaBackend(
                    model=settings['model'],
                    base_url=settings['base_url']
                )
            elif backend_type == 'openai':
                return OpenAIBackend(
                    model=settings['model']
                )
            elif backend_type == 'groq':
                return GroqBackend(
                    model=settings['model']
                )
            else:
                log(f"Unknown backend type: {backend_type}, falling back to Ollama", 'warning')
                return OllamaBackend()
        except Exception as e:
            log(f"Error initializing {backend_type} backend: {e}, falling back to Ollama", 'warning')
            return OllamaBackend()
    
    def switch_backend(self, backend_type: str, settings: Dict[str, Any] = None):
        """Switch to a different backend."""
        if backend_type not in ['ollama', 'openai', 'groq']:
            raise ValueError(f"Unsupported backend type: {backend_type}")
        
        if settings:
            self.config['backend_settings'][backend_type].update(settings)
        
        self.config['backend'] = backend_type
        self.backend = self._initialize_backend()
        self._save_config()
        log(f"Switched to {backend_type} backend")

    def _setup_hotkey_listener(self):
        import threading
        import pynput
        from pynput import keyboard
        hotkeys = [
            '<ctrl>+<alt>+j',
            '<ctrl>+<shift>+j',
        ]
        def on_activate():
            log("Hotkey pressed! Showing URL input dialog.")
            show_notification("JobOps", "Hotkey pressed! Opening dialog...")
            # Schedule dialog in main thread
            self.root.after(0, self._show_url_input)
        def for_canonical(f):
            return lambda k: f(self.listener.canonical(k))
        def listen():
            for hotkey_str in hotkeys:
                try:
                    hotkey = keyboard.HotKey(
                        keyboard.HotKey.parse(hotkey_str),
                        on_activate
                    )
                    log(f"Registering hotkey: {hotkey_str}")
                    break
                except Exception as e:
                    log(f"Failed to register hotkey {hotkey_str}: {e}", 'warning')
            else:
                log("No hotkey could be registered!", 'error')
                return
            with keyboard.Listener(
                on_press=for_canonical(hotkey.press),
                on_release=for_canonical(hotkey.release)) as listener:
                self.listener = listener
                listener.join()
        threading.Thread(target=listen, daemon=True).start()

    def _show_url_input(self):
        import tkinter as tk
        from tkinter import ttk, simpledialog, messagebox
        class URLInputDialog(simpledialog.Dialog):
            def __init__(self, parent, app):
                self.app = app
                self.result = None
                super().__init__(parent, title="Job URL Input")
            def body(self, master):
                ttk.Label(master, text="Backend:").grid(row=0, column=0, sticky='w')
                self.backend_var = tk.StringVar(value=self.app.config['backend'])
                backend_combo = ttk.Combobox(
                    master, textvariable=self.backend_var,
                    values=['ollama', 'openai', 'groq'], state='readonly')
                backend_combo.grid(row=0, column=1, sticky='ew')
                backend_combo.bind('<<ComboboxSelected>>', self.on_backend_change)
                ttk.Label(master, text="Model:").grid(row=1, column=0, sticky='w')
                self.model_var = tk.StringVar()
                self.model_entry = ttk.Entry(master, textvariable=self.model_var)
                self.model_entry.grid(row=1, column=1, sticky='ew')
                ttk.Label(master, text="URL:").grid(row=2, column=0, sticky='w')
                self.url_var = tk.StringVar()
                url_entry = ttk.Entry(master, textvariable=self.url_var)
                url_entry.grid(row=2, column=1, sticky='ew')
                self.update_model_field()
                return url_entry
            def update_model_field(self):
                backend = self.backend_var.get()
                settings = self.app.config['backend_settings'][backend]
                self.model_var.set(settings['model'])
            def on_backend_change(self, event):
                self.update_model_field()
            def validate(self):
                if not self.url_var.get():
                    messagebox.showerror("Error", "Please enter a URL", parent=self)
                    return False
                return True
            def apply(self):
                backend = self.backend_var.get()
                model = self.model_var.get()
                url = self.url_var.get()
                if backend != self.app.config['backend'] or model != self.app.config['backend_settings'][backend]['model']:
                    self.app.switch_backend(backend, {'model': model})
                self.result = url
        dialog = URLInputDialog(self.root, self)
        if dialog.result:
            try:
                job_data = self.job_scraper.scrape_job_description(dialog.result)
                letter = self._generate_letter(job_data)
                self._save_letter(job_data, letter)
                from tkinter import messagebox
                messagebox.showinfo("Success", "Motivation letter generated and saved!", parent=self.root)
            except Exception as e:
                from tkinter import messagebox
                messagebox.showerror("Error", str(e), parent=self.root)

    def _generate_letter(self, job_data):
        resumes = get_latest_resume()
        if not resumes:
            raise Exception("No resume found in the database. Please upload a resume document first.")
        resume_data = resumes[0]
        prompt = f"""Write a motivation letter in markdown for the following job:\n\nTitle: {job_data.get('title', '')}\nCompany: {job_data.get('company', '')}\nURL: {job_data.get('url', '')}\n\nDescription:\n{job_data.get('description', '')}\n\nRequirements:\n{job_data.get('requirements', '')}\n\nResume Data:\n{resume_data}\n"""
        return self.backend.generate_response(prompt)

    def _save_letter(self, job_data, letter):
        import datetime
        company = job_data.get('company', 'Unknown').replace(' ', '_')
        title = job_data.get('title', 'Unknown').replace(' ', '_')
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"motivation_{company}_{title}_{timestamp}.md"
        filepath = os.path.join(AppConstants.MOTIVATIONS_DIR, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(letter)

    def run(self):
        # Start tray icon in a thread
        tray_thread = threading.Thread(target=self._run_tray, daemon=True)
        tray_thread.start()
        # Start Tkinter event loop in main thread
        self.root.mainloop()
        tray_thread.join()

    def _run_tray(self):
        """Run the system tray icon with Generate, Upload Document, and Exit menu items."""
        def create_icon():
            # Simple green document icon
            image = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
            dc = ImageDraw.Draw(image)
            dc.rectangle((12, 8, 48, 56), fill='#4CAF50', outline='#2E7D32')
            dc.polygon([(48, 8), (48, 20), (36, 8)], fill='#2E7D32')
            dc.line([(18, 24), (42, 24)], fill='white', width=2)
            dc.line([(18, 30), (42, 30)], fill='white', width=2)
            dc.line([(18, 36), (36, 36)], fill='white', width=2)
            return image
        def on_exit(icon, item):
            icon.stop()
            log("Application exited by user")
        def on_generate(icon, item):
            log("Generate menu clicked! Showing URL input dialog.")
            show_notification("JobOps", "Opening dialog via tray menu...")
            self._show_url_input()
        def on_upload(icon, item):
            log("Upload Document menu clicked! Opening file dialog.")
            show_notification("JobOps", "Upload a document...")
            self._upload_document()
        menu = pystray.Menu(
            pystray.MenuItem('Generate', on_generate),
            pystray.MenuItem('Upload Document', on_upload),
            pystray.MenuItem('Exit', on_exit)
        )
        icon = pystray.Icon(AppConstants.APP_NAME, create_icon(), AppConstants.APP_NAME, menu)
        icon.run()

    def _upload_document(self):
        import tkinter as tk
        from tkinter import filedialog, simpledialog, messagebox
        import pdfplumber
        import datetime
        root = tk.Tk()
        root.withdraw()
        filetypes = [
            ("PDF files", "*.pdf"),
            ("Markdown files", "*.md"),
            ("Text files", "*.txt"),
            ("All files", "*.*")
        ]
        filepath = filedialog.askopenfilename(title="Select Document", filetypes=filetypes)
        if not filepath:
            root.destroy()
            return
        # Ask for document type
        doc_type = simpledialog.askstring(
            "Document Type",
            f"Enter document type ({', '.join(DocumentType.ALL)}):",
            initialvalue=DocumentType.RESUME
        )
        if not doc_type or doc_type not in DocumentType.ALL:
            messagebox.showerror("Error", f"Invalid document type. Must be one of: {', '.join(DocumentType.ALL)}")
            root.destroy()
            return
        # Extract raw content
        try:
            if filepath.lower().endswith('.pdf'):
                with pdfplumber.open(filepath) as pdf:
                    raw_content = "\n".join(page.extract_text() or '' for page in pdf.pages)
            else:
                with open(filepath, 'r', encoding='utf-8') as f:
                    raw_content = f.read()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to extract content: {e}")
            root.destroy()
            return
        # Use LLM to structure content
        try:
            prompt = f"""Extract and structure the following document as JSON. Identify fields such as name, contact, experience, education, skills, etc. If it's a resume, use a standard resume schema.\n\nDocument:\n{raw_content[:4000]}"""
            structured_content = self.backend.generate_response(prompt)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to structure document: {e}")
            root.destroy()
            return
        # Store in DB
        try:
            conn = sqlite3.connect(get_db_path())
            c = conn.cursor()
            c.execute(
                "INSERT INTO documents (type, filename, raw_content, structured_content, uploaded_at) VALUES (?, ?, ?, ?, ?)",
                (doc_type, os.path.basename(filepath), raw_content, structured_content, datetime.datetime.now().isoformat())
            )
            conn.commit()
            conn.close()
            messagebox.showinfo("Success", "Document uploaded and structured successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save to database: {e}")
        root.destroy()

# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def main():
    """Main entry point."""
    try:
        log(f"Starting {AppConstants.APP_NAME} v{AppConstants.VERSION}")
        
        # Check dependencies
        missing_deps = []
        if not OPENAI_AVAILABLE:
            missing_deps.append("openai")
        if not OLLAMA_AVAILABLE:
            missing_deps.append("ollama")
        if not GROQ_AVAILABLE:
            missing_deps.append("groq")
        
        if missing_deps:
            log(f"Optional dependencies not installed: {', '.join(missing_deps)}")
            print(f"Note: Some backends not available. Install with: pip install {' '.join(missing_deps)}")
        
        # Initialize and run application
        app = MotivationLetterApp()
        app.run()
        
    except KeyboardInterrupt:
        log("Application interrupted by user")
    except Exception as e:
        log(f"Application error: {e}", 'error')
        raise
    finally:
        log("Application ended")

def get_latest_resume():
    """Fetch the most recent resume(s) from the documents table. Returns a list of resumes (dicts)."""
    conn = sqlite3.connect(get_db_path())
    c = conn.cursor()
    c.execute("SELECT structured_content FROM documents WHERE type = ? ORDER BY uploaded_at DESC", (DocumentType.RESUME,))
    rows = c.fetchall()
    conn.close()
    resumes = []
    for row in rows:
        try:
            import json as _json
            data = _json.loads(row[0])
            if isinstance(data, list):
                resumes.extend(data)
            else:
                resumes.append(data)
        except Exception:
            continue
    return resumes  # Return empty list if none found

if __name__ == "__main__":
    main()
