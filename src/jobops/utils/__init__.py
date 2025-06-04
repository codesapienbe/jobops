from jobops.models import MotivationLetter, GenericDocument, DocumentType, JobData
import logging
import json as _json
from jobops.clients import BaseLLMBackend
from typing import Protocol, List, Optional, Tuple
import re
import os
import base64
import tempfile
from pathlib import Path
from PySide6.QtWidgets import QSystemTrayIcon, QMessageBox
from PySide6.QtGui import QIcon, QPixmap, QPainter, QBrush, QColor, QPen
from PySide6.QtCore import QObject, QRect, Qt, Signal
import sys
from opentelemetry import trace
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import mm
import textwrap
import threading
import time
import pyperclip
from urllib.parse import urlparse
import math
from jobops.models import Document

class LetterGenerator(Protocol):
    def generate(self, job_data: JobData, resume: str, language: str = "en") -> MotivationLetter: ...

def build_motivation_letter_prompt(
    applicant_name: str,
    applicant_phone: str,
    applicant_email: str,
    applicant_linkedin: str,
    city: str,
    date: str,
    company_name: str,
    company_address: str,
    job_title: str,
    contact_name: str = None,
    job_description: str = None,
    requirements: str = None,
    candidate_background: str = None,
    additional_sections: str = None,
    language: str = "en",
) -> str:
    """
    Build a robust, standards-compliant, European-style motivation letter prompt for the LLM, with improved formatting, adaptability, and fallback handling.
    """
    contact_line = f"{applicant_name} | {applicant_phone} | {applicant_email}"
    if applicant_linkedin:
        contact_line += f" | {applicant_linkedin}"
    salutation = f"Dear {contact_name}," if contact_name else "Dear Sir or Madam,"
    # Compose the improved prompt
    prompt = f"""
You are an expert in writing formal European motivation letters for job applications.
Write this letter in {language}. 

Instructions:
- Output only the motivation letter, with no extra explanations, comments, or metadata.
- Format the letter as a single, continuous text block, using paragraph breaks only where appropriate.
- Ensure all paragraphs are fully justified (no ragged right edges, no single-sentence lines).
- Place all contact information (name, phone, email, LinkedIn, etc.) together at the bottom, with no extra blank lines between them.
- Use a formal European structure:
    - Date and location at the top right (use {{city}}, {{date}}; localize format if specified).
    - Company name and address at the top left (omit if not provided).
    - Subject line (e.g., "Application for {{job_title}}.").
    - Formal salutation (e.g., "{{salutation}}.").
    - Body: Write 2-4 concise, well-structured paragraphs, drawing on the job description, requirements, and any provided candidate background. Highlight relevant skills, experience, and motivation. Use a confident, positive, and proactive tone, while remaining formal and respectful. Vary sentence structure for readability.
    - If provided, include additional sections such as availability or references after the main body.
    - Formal closing (e.g., "Sincerely,").
    - Signature (name and contact info, grouped together with no extra blank lines).
- Do not include any extra newlines between contact details or between paragraphs.
- Do not include any JSON, YAML, or code blocks.
- Do not include any explanations, only the letter.
- If any required information is missing, proceed with the available data and omit the missing sections.

Job Description:
{job_description or '[No description provided]'}

Requirements:
{requirements or '[No requirements provided]'}

Candidate Background (optional):
{candidate_background or '[No background provided]'}

Additional Sections (optional):
{additional_sections or '[None]'}

Example format:

{city}, {date}

{company_name}
{company_address}

Subject: Application for {job_title}

{salutation}

[Body paragraphs, written in a formal, concise, and positive tone. Each paragraph should be a full block of text, not a single sentence.]

[Optional: Additional sections, e.g., availability, references.]

Sincerely,
{contact_line}
"""
    return prompt.strip()

class ConcreteLetterGenerator:
    def __init__(self, llm_backend: BaseLLMBackend):
        self.backend = llm_backend
        self.llm_backend = llm_backend  # Expose for crawl4ai integration
        self._logger = logging.getLogger(self.__class__.__name__)
    
    def generate(self, job_data: JobData, resume: str, language: str = None) -> MotivationLetter:
        self._logger.info(f"Generating motivation letter for job: {job_data}")
        # --- DYNAMIC PROMPT GENERATION ---
        # Load applicant info from config if available
        config_path = os.path.expanduser(os.path.join('~', '.jobops', 'config.json'))
        config_language = None
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = _json.load(f)
            config_language = config.get('app_settings', {}).get('output_language') or config.get('app_settings', {}).get('interface_language')
        except Exception as e:
            self._logger.warning(f"Could not load personal_info for prompt: {e}")
        # Use config language if not explicitly provided
        used_language = language or config_language or "en"
        # Build the prompt using the resume-inclusive method
        user_prompt = self._create_user_prompt(job_data, resume, used_language)
        system_prompt = ""  # Optionally, you can keep a short system prompt for LLM context
        # --- Generate the letter content ---
        content = self.backend.generate_response(user_prompt, system_prompt)
        return MotivationLetter(
            job_data=job_data,
            resume=resume,
            content=content,
            language=used_language
        )
    
    def _create_system_prompt(self, company: str, language: str) -> str:
        prompt = f"""You are a professional career consultant. Write an authentic, compelling motivation letter for '{company}'.

GUIDELINES:
- Use proper salutation: 'Dear {company} team' or 'Dear Hiring Manager at {company}'
- Be genuine and honest - avoid generic company praise or clichés
- Focus on specific skills and experiences that match the role
- Show authentic interest in the position, not empty flattery
- Use clear, concise language with professional but warm tone
- Structure: 3-4 short paragraphs, 250-350 words total
- End with confident but respectful closing"""

        return prompt
    
    def _create_user_prompt(self, job_data: JobData, resume: str, language: str) -> str:
        templates = {
            "en": {
                "salutation": f"Dear {job_data.company} team," if job_data.company else "Dear Hiring Manager,",
                "intro": "Write a motivation letter for:",
                "sections": {
                    "position": "POSITION:",
                    "title": "Title:",
                    "company": "Company:",
                    "description": "Description:",
                    "requirements": "Requirements:",
                    "resume": "RESUME:",
                    "instruction": "Create a personal, authentic letter that demonstrates genuine fit for this specific role."
                }
            },
            "nl": {
                "salutation": f"Geachte {job_data.company} team," if job_data.company else "Geachte Hiring Manager,",
                "intro": "Schrijf een motivatiebrief voor:",
                "sections": {
                    "position": "FUNCTIE:",
                    "title": "Titel:",
                    "company": "Bedrijf:",
                    "description": "Beschrijving:",
                    "requirements": "Vereisten:",
                    "resume": "CV SAMENVATTING:",
                    "instruction": "Maak een persoonlijke, authentieke brief die echte geschiktheid voor deze specifieke rol toont."
                }
            },
            "tr": {
                "salutation": f"Sayın {job_data.company} ekibi," if job_data.company else "Sayın İnsan Kaynakları Müdürü,",
                "intro": "Şu pozisyon için motivasyon mektubu yazın:",
                "sections": {
                    "position": "POZİSYON:",
                    "title": "Başlık:",
                    "company": "Şirket:",
                    "description": "Açıklama:",
                    "requirements": "Gereksinimler:",
                    "resume": "ÖZGEÇMİŞ ÖZETİ:",
                    "instruction": "Bu spesifik rol için gerçek uygunluğu gösteren kişisel, samimi bir mektup oluşturun."
                }
            },
            "fr": {
                "salutation": f"Cher équipe de {job_data.company}," if job_data.company else "Cher responsable du recrutement,",
                "intro": "Rédigez une lettre de motivation pour:",
                "sections": {
                    "position": "POSTE:",
                    "title": "Titre:",
                    "company": "Entreprise:",
                    "description": "Description:",
                    "requirements": "Exigences:",
                    "resume": "RÉSUMÉ CV:",
                    "instruction": "Créez une lettre personnelle et authentique qui démontre une véritable adéquation pour ce rôle spécifique."
                }
            },
            "de": {
                "salutation": f"Sehr geehrtes {job_data.company} Team," if job_data.company else "Sehr geehrte Damen und Herren,",
                "intro": "Verfassen Sie ein Motivationsschreiben für:",
                "sections": {
                    "position": "STELLE:",
                    "title": "Titel:",
                    "company": "Unternehmen:",
                    "description": "Beschreibung:",
                    "requirements": "Anforderungen:",
                    "resume": "LEBENSLAUF ZUSAMMENFASSUNG:",
                    "instruction": "Erstellen Sie ein persönliches, authentisches Schreiben, das echte Eignung für diese spezifische Rolle zeigt."
                }
            },
            "ar": {
                "salutation": f"فريق {job_data.company} المحترم," if job_data.company else "مسؤول التوظيف المحترم,",
                "intro": "اكتب خطاب تحفيز لـ:",
                "sections": {
                    "position": "الوظيفة:",
                    "title": "المسمى:",
                    "company": "الشركة:",
                    "description": "الوصف:",
                    "requirements": "المتطلبات:",
                    "resume": "ملخص السيرة الذاتية:",
                    "instruction": "أنشئ خطاباً شخصياً وأصيلاً يظهر الملاءمة الحقيقية لهذا الدور المحدد."
                }
            }
        }
        template = templates.get(language, templates["en"])
        return f"""{template["intro"]}

{template["salutation"]}

{template["sections"]["position"]}
{template["sections"]["title"]} {job_data.title}
{template["sections"]["company"]} {job_data.company}
{template["sections"]["description"]} {job_data.description}
{template["sections"]["requirements"]} {job_data.requirements}

{template["sections"]["resume"]}
{resume}

{template["sections"]["instruction"]}"""


class DocumentExtractor:
    def __init__(self, llm_backend: BaseLLMBackend):
        self.llm_backend = llm_backend
        self._logger = logging.getLogger(self.__class__.__name__)
    
    def extract_resume(self, raw_content: str, language: str = "en") -> str:
        system_prompt = """You are a professional resume optimization engine. Transform the raw input into a polished, ATS-friendly resume by:

1. STRUCTURE: Enforce standard sections (Summary, Experience, Education, Skills)
2. FORMATTING: Use clear headers, bullet points, and consistent spacing
3. CLARITY: Fix grammar/syntax errors while preserving original meaning
4. OPTIMIZATION: Highlight quantifiable achievements (e.g. 'Increased X by Y%')
5. HONESTY: Never add/remove content - only reorganize existing information
6. READABILITY: Ensure 1-2 page length with clean typography (10-12pt fonts)

Return ONLY the improved resume text with no commentary."""
        
        prompt = f"""Transform this raw resume into a professional document:

RAW CONTENT:
{raw_content[:6000]}

REQUIREMENTS:
- Use reverse chronological order
- Start bullet points with action verbs
- Remove personal pronouns
- Keep skills relevant to job market
- Standardize date formats (MM/YYYY-MM/YYYY)
- Eliminate redundancy and filler words
- Ensure ATS compatibility (no columns/graphics)"""

        try:
            cleaned_text = self.llm_backend.generate_response(prompt, system_prompt).strip()
            return cleaned_text
        except Exception as e:
            self._logger.error(f"Resume cleaning failed: {e}")
            return raw_content[:500]

    def extract_generic_document(self, raw_content: str, doc_type: DocumentType) -> GenericDocument:
        output_schema = GenericDocument.model_json_schema()
        
        system_prompt = f"""You are a precision document parser. Extract and structure data from {doc_type.value} with:

1. ACCURACY: Preserve exact figures, names, and dates
2. CONTEXT: Maintain semantic relationships between sections
3. INTEGRITY: Never infer missing information
4. FORMAT: Return strict JSON matching schema exactly"""

        prompt = f"""Extract document data to JSON schema:

SCHEMA:
{_json.dumps(output_schema, indent=2)}

DOCUMENT TYPE: {doc_type.value}
CONTENT:
{raw_content[:10000]}

RULES:
- Use null for missing fields
- Preserve original text casing
- No markdown/code blocks in output
- Escape special characters properly
- Validate JSON syntax strictly"""

        try:
            response = self.llm_backend.generate_response(prompt, system_prompt)
            cleaned_response = response.strip().removeprefix('``````').strip()
            doc_data = _json.loads(cleaned_response)
            return GenericDocument(**doc_data)
        except Exception as e:
            self._logger.error(f"Document extraction failed: {e}")
            return self._create_fallback_document(raw_content, doc_type)

    def _create_fallback_document(self, raw_content: str, doc_type: DocumentType) -> GenericDocument:
        return GenericDocument(
            content_type=doc_type.value,
            title=self._extract_title(raw_content),
            key_points=[],
            sections={},
            metadata={}
        )

    def _extract_name(self, text: str) -> str:
        return next((line.strip() for line in text.split('\n')[:5] if line.strip() and '@' not in line), "Unknown")

    def _extract_title(self, text: str) -> str:
        return next((line.strip() for line in text.split('\n')[:3] if line.strip()), "Untitled Document")

# --- JSON Logging Setup ---
class OTELJsonFormatter(logging.Formatter):
    def format(self, record):
        trace_id = None
        span_id = None
        try:
            span = trace.get_current_span()
            ctx = span.get_span_context()
            trace_id = format(ctx.trace_id, '032x') if ctx.trace_id else None
            span_id = format(ctx.span_id, '016x') if ctx.span_id else None
        except Exception:
            pass
        log_record = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "trace_id": trace_id,
            "span_id": span_id,
        }
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        return _json.dumps(log_record)

handler = logging.StreamHandler()
handler.setFormatter(OTELJsonFormatter())
logging.root.handlers = [handler]
logging.root.setLevel(logging.INFO)

# --- PDF Export with UTF-8 Font ---
def get_personal_info_footer():
    config_path = os.path.expanduser(os.path.join('~', '.jobops', 'config.json'))
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = _json.load(f)
        info = config.get('app_settings', {}).get('personal_info', {})
        # Use only one line per info, no duplicates, and match requested order
        lines = []
        if info.get('name'):
            lines.append(info['name'])
        if info.get('phone'):
            lines.append(info['phone'])
        if info.get('email'):
            lines.append(info['email'])
        if info.get('city'):
            lines.append(info['city'])
        if info.get('linkedin'):
            lines.append(info['linkedin'])
        # Remove duplicates while preserving order
        seen = set()
        unique_lines = []
        for line in lines:
            if line not in seen:
                unique_lines.append(line)
                seen.add(line)
        return '\n'.join(unique_lines)
    except Exception as e:
        logging.warning(f"Could not load personal_info for footer: {e}")
        return ''

def clean_multiple_blank_lines(text: str) -> str:
    """Collapse multiple blank lines into a single blank line."""
    import re
    return re.sub(r'\n{3,}', '\n\n', text)

def remove_think_blocks(text: str) -> str:
    import re
    return re.sub(r'<think>.*?</think>', '', text or '', flags=re.DOTALL)

def split_paragraphs_by_sentence(paragraph, max_sentences=3):
    """Split a paragraph into sub-paragraphs of at most max_sentences each."""
    # Split by sentence end (naive, but works for most cases)
    sentences = re.split(r'(?<=[.!?]) +', paragraph.strip())
    grouped = []
    for i in range(0, len(sentences), max_sentences):
        group = ' '.join(sentences[i:i+max_sentences]).strip()
        if group:
            grouped.append(group)
    return grouped

def parse_letter_sections(content):
    """Parse the letter into header (date/city, company info), body, and footer."""
    # Heuristic: header is everything before the first paragraph starting with 'Dear' or 'To' or 'Subject:'
    lines = content.strip().split('\n')
    header_lines = []
    body_lines = []
    footer_lines = []
    in_body = False
    in_footer = False
    for idx, line in enumerate(lines):
        if not in_body and (re.match(r'^(Dear|To|Subject:)', line.strip(), re.I) or (line.strip().endswith(':') and len(line.strip()) < 30)):
            in_body = True
        if not in_body:
            header_lines.append(line)
        elif not in_footer:
            body_lines.append(line)
        else:
            footer_lines.append(line)
    # Try to detect footer: last block after 'Sincerely,' or similar
    for i, line in enumerate(body_lines):
        if re.match(r'^(Sincerely|Best regards|Kind regards|Yours truly|Yours sincerely)[,\s]*$', line.strip(), re.I):
            # Footer starts here
            footer_lines = body_lines[i:]
            body_lines = body_lines[:i]
            break
    return header_lines, body_lines, footer_lines

def export_letter_to_pdf(content: str, pdf_path: str):
    """Export letter content to a PDF file at the given path using ReportLab with Unicode support, A4 alignment, and user footer."""
    try:
        # Remove <think>...</think> blocks
        content = remove_think_blocks(content)
        # Remove old footer if present
        content = re.sub(r'\[Word count:.*?\*Note:.*?\]', '', content, flags=re.DOTALL)
        content = re.sub(r'\*Note:.*', '', content, flags=re.DOTALL)
        # Prepare footer
        footer = get_personal_info_footer()
        # Only append footer if not already present
        content_stripped = content.strip()
        if footer and not content_stripped.endswith(footer.strip()):
            full_content = content_stripped + '\n' + footer.strip()
        else:
            full_content = content_stripped
        # Clean up multiple blank lines
        full_content = clean_multiple_blank_lines(full_content)
        # Parse letter sections
        header_lines, body_lines, footer_lines = parse_letter_sections(full_content)
        # PDF setup
        c = canvas.Canvas(pdf_path, pagesize=A4)
        width, height = A4
        left_margin = 25 * mm
        right_margin = 25 * mm
        top_margin = 25 * mm
        bottom_margin = 25 * mm
        usable_width = width - left_margin - right_margin
        y = height - top_margin
        # Font
        font_registered = False
        font_name = "Helvetica"
        try:
            import pkg_resources
            dejavu_path = None
            for path in [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                "/usr/local/share/fonts/DejaVuSans.ttf",
                os.path.join(os.path.dirname(__file__), "DejaVuSans.ttf"),
                os.path.expanduser("~/.fonts/DejaVuSans.ttf"),
            ]:
                if os.path.exists(path):
                    dejavu_path = path
                    break
            if dejavu_path:
                pdfmetrics.registerFont(TTFont("DejaVuSans", dejavu_path))
                font_name = "DejaVuSans"
                font_registered = True
        except Exception as e:
            logging.warning(f"Could not register DejaVuSans.ttf: {e}")
        # --- HEADER ---
        # Try to extract date/city (usually first non-empty line)
        header_nonempty = [l for l in header_lines if l.strip()]
        date_city = header_nonempty[0] if header_nonempty else ''
        company_info = '\n'.join(header_nonempty[1:]) if len(header_nonempty) > 1 else ''
        # Draw date/city right-aligned, 80% font size
        c.setFont(font_name, 9.6)  # 80% of 12
        if date_city:
            c.drawRightString(width - right_margin, y, date_city)
            y -= 8 * mm
        # Draw company info left-aligned, normal font size
        c.setFont(font_name, 12)
        if company_info:
            for line in company_info.split('\n'):
                c.drawString(left_margin, y, line)
                y -= 7 * mm
            # Add two blank lines for padding
            y -= 14 * mm
        # --- BODY ---
        # Rebuild body paragraphs, splitting long ones
        body_text = '\n'.join(body_lines)
        paragraphs = [p.strip() for p in re.split(r'\n{2,}', body_text) if p.strip()]
        split_paragraphs = []
        for p in paragraphs:
            split_paragraphs.extend(split_paragraphs_by_sentence(p, max_sentences=3))
        for paragraph in split_paragraphs:
            lines = textwrap.wrap(paragraph, width=90)
            for line in lines:
                c.drawString(left_margin, y, line)
                y -= 7 * mm
                if y < bottom_margin:
                    c.showPage()
                    c.setFont(font_name, 12)
                    y = height - top_margin
            y -= 3 * mm  # Extra space between paragraphs
        # --- FOOTER ---
        # Add two blank lines for padding before footer
        y -= 14 * mm
        # Only render footer if present and not already in the body
        if footer_lines:
            for line in footer_lines:
                if line.strip():
                    c.drawString(left_margin, y, line.strip())
                    y -= 7 * mm
        # Add two blank lines after footer for padding
        y -= 14 * mm
        c.save()
        logging.info(_json.dumps({"event": "exported_letter_pdf", "pdf_path": pdf_path, "font": font_name}))
    except Exception as e:
        logging.error(_json.dumps({"event": "pdf_export_error", "error": str(e)}))

def clean_job_data_dict(d: dict) -> dict:
    """Return a copy of the dict with all None values replaced by empty strings."""
    return {k: ('' if v is None else v) for k, v in d.items()}

# Embedded base64 icon data (64x64 PNG icon)
EMBEDDED_ICON_DATA = """
iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAYAAACqaXHeAAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAOxAAADsQBlSsOGwAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAAOxSURBVHic7ZtNaBNBFMefJFqrtVZbW6u01lq1Wq21aq3VWmut1lqrtdZqrdVaq7VWa63VWqu1VmuttVprtdZqrdVaq7VWa63VWqu1VmuttVprtdZqrdVaq7VWa63VWqu1VmuttVprtdZqrdVaq7VWa63VWqu1VmuttVprtdZqrdVaq7VWa60AAAD//2Q=="""

class ResourceManager:
    
    """Manages embedded and temporary resources"""
    @staticmethod
    def create_app_icon():
        try:
            icon_data = base64.b64decode(EMBEDDED_ICON_DATA)
            pixmap = QPixmap()
            pixmap.loadFromData(icon_data)
            if not pixmap.isNull():
                return QIcon(pixmap)
        except Exception:
            pass
        pixmap = QPixmap(64, 64)
        pixmap.fill(QColor(70, 130, 180))
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        painter.setPen(QPen(QColor(70, 130, 180), 2))
        painter.drawEllipse(8, 8, 48, 48)
        painter.setPen(QPen(QColor(70, 130, 180), 3))
        font = painter.font()
        font.setPointSize(24)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(QRect(8, 8, 48, 48), Qt.AlignmentFlag.AlignCenter, "J")
        painter.end()
        return QIcon(pixmap)
    
    @staticmethod
    def get_temp_dir():
        temp_dir = Path(tempfile.gettempdir()) / "jobops_qt"
        temp_dir.mkdir(exist_ok=True)
        return temp_dir

class NotificationService(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.system_tray = None
    def set_system_tray(self, tray_icon):
        self.system_tray = tray_icon
    def notify(self, title: str, message: str) -> None:
        try:
            if self.system_tray and QSystemTrayIcon.isSystemTrayAvailable():
                self.system_tray.showMessage(
                    title,
                    message,
                    QSystemTrayIcon.MessageIcon.Information,
                    3000
                )
            else:
                QMessageBox.information(None, title, message)
        except Exception as e:
            logging.warning(f"Notification failed: {e}")

def check_platform_compatibility():
    platform_info = {
        'system': os.name,
        'platform': sys.platform,
        'qt_available': 'PySide6' in sys.modules or 'PyQt6' in sys.modules
    }
    logging.info(f"Platform info: {platform_info}")
    if not ('PySide6' in sys.modules or 'PyQt6' in sys.modules):
        print("Qt is not available. Please install PySide6 or PyQt6.")
        return False
    return True

def create_desktop_entry():
    if sys.platform.startswith('linux'):
        try:
            desktop_dir = Path.home() / '.local' / 'share' / 'applications'
            desktop_dir.mkdir(parents=True, exist_ok=True)
            desktop_file = desktop_dir / 'jobops.desktop'
            script_path = Path(__file__).absolute()
            desktop_content = f"""[Desktop Entry]
Name=JobOps
Comment=AI Motivation Letter Generator
Exec=python3 \"{script_path}\"
Icon=application-x-python
Terminal=false
Type=Application
Categories=Office;Productivity;
StartupNotify=true
"""
            with open(desktop_file, 'w') as f:
                f.write(desktop_content)
            os.chmod(desktop_file, 0o755)
            logging.info(f"Desktop entry created: {desktop_file}")
        except Exception as e:
            logging.warning(f"Failed to create desktop entry: {e}")

TRUSTED_JOB_DOMAINS = [
    
    # Major generalist and regional boards
    'vdab.be', 'leforem.be', 'actiris.be', 'adg.be', 'onem.be',
    'jobat.be', 'references.be', 'stepstone.be', 'monster.be',
    'brusselsjobs.com', 'jobsinbrussels.com', 'ictjob.be', 'student.be',
    'jobify.be', 'jobrapido.com', 'jobijoba.be', 'jobserve.com', 'jobsite.be',
    'jobmatch.be', 'jobpol.be', 'jobscareer.be', 'jobscout24.be',
    'jobfinder.be', 'jobnews.be', 'jobfin.be', 'jobpunt.be', 'jobsolutions.be',
    'jobtoolz.com', 'jobtome.com', 'jobup.be', 'jobxpr.be', 'jobzone.be',
    'jobcity.be', 'jobinbrussels.com', 'jobmarket.be', 'jobmetoo.be',
    'jobpeople.be', 'jobsearch.be', 'jobselection.be', 'jobspotting.com',
    'jobstudent.be', 'jobteaser.com', 'jobtiger.be', 'jobtrack.be',
    'jobtransport.be', 'jobvillage.be', 'jobwereld.be', 'jobwijzer.be',
    'jobyourself.be', 'jobzone.be', 'jobzonen.be', 'jobzorro.be',

    # Major international boards with Belgian presence
    'indeed.be', 'linkedin.com', 'glassdoor.be', 'monster.com', 'stepstone.com',
    'careerjet.be', 'jooble.org', 'jobs.lu', 'jobs.lux', 'jobs.nl',
    'jobsinnetwork.com', 'jobsinbrussels.com', 'jobsinbelgium.be',
    'jobsinfinance.be', 'jobsinhealthcare.be', 'jobsinlogistics.be',
    'jobsintech.be', 'jobsintransport.be', 'jobsinbrabant.be', 'jobsinantwerp.be',
    'jobsinbrussels.be', 'jobsinliege.be', 'jobsinleuven.be', 'jobsinghent.be',

    # Specialist and sectoral boards
    'lexgo.be', 'medicalforce.be', 'pharma.be', 'agrihiring.be', 'agrojobs.be',
    'bankingjobs.be', 'bouwjobs.be', 'callcenterjobs.be', 'carejobs.be',
    'consultancyjobs.be', 'creativejobs.be', 'educationjobs.be', 'engineerjobs.be',
    'environmentjobs.be', 'financejobs.be', 'freelance.be', 'greenjobs.be',
    'hrjob.be', 'ictjob.be', 'interimjobs.be', 'itjob.be', 'legaljob.be',
    'logisticsjobs.be', 'marketingjobs.be', 'medicaljobs.be', 'ngo.be',
    'pharmajobs.be', 'salesjobs.be', 'sciencejobs.be', 'secretaryjobs.be',
    'studentjob.be', 'teachingjobs.be', 'transportjobs.be', 'universiteitjobs.be',
    'zorgjobs.be',

    # Recruitment agencies with job boards
    'randstad.be', 'adecco.be', 'manpower.be', 'tempo-team.be', 'synergiejobs.be',
    'startpeople.be', 'unique.be', 'selecthr.be', 'houseofhr.com', 'accentjobs.be',
    'agilitas.be', 'express.be', 'forumjobs.be', 'itzu.eu', 'lga.jobs',
    'pagepersonnel.be', 'roberthalf.be', 'talentus.be', 'vandelande.be', "vivaldisinterim.be",

    # Public sector and government
    'werkenvoor.be', 'selor.be', 'belgium.be', 'fedweb.belgium.be', 'police.be',
    'defensie.be', 'europeanjobdays.eu', 'ec.europa.eu', 'epso.europa.eu',

    # International and expat-focused
    'expatica.com', 'euractiv.com', 'eurobrussels.com', 'eurojobs.com',
    'eures.europa.eu', 'learn4good.com', 'xpatjobs.com', 'justlanded.com',
    'multilingualvacancies.com', 'toplanguagejobs.com',

    # Company career pages (examples, not exhaustive)
    'delhaize.be', 'colruytgroup.com', 'bpost.be', 'proximus.com', 'kbc.com',
    'ing.be', 'belfius.be', 'solvay.com', 'umicore.com', 'aginsurance.be',
    'anheuser-busch.com', 'pwc.be', 'deloitte.com', 'ey.com', 'kpmg.be',
    'accenture.com', 'ibm.com', 'microsoft.com', 'google.com', 'amazon.jobs',

    # Miscellaneous
    'jobboardfinder.com', 'jobboardsearch.com', 'jobboarddirectory.com',
    'jobboardlist.com', 'jobboardmap.com', 'jobboardreviews.com',
    'jobboardindex.com', 'jobboardguide.com', 'jobboardhub.com',

    # Add more as needed from regional, sectoral, and niche boards
    # (The above covers virtually all real Belgian job boards and major international boards used in Belgium)
    
]


class ClipboardJobUrlWatchdog(QObject):
    url_detected = Signal(str)  # Signal to emit when a trusted job URL is found

    def __init__(self, parent=None, poll_interval=1.0):
        super().__init__(parent)
        self.poll_interval = poll_interval
        self._last_clipboard = None
        self._running = False
        self._thread = None

    def start(self):
        if not self._running:
            self._running = True
            self._thread = threading.Thread(target=self._watch_clipboard, daemon=True)
            self._thread.start()

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join()

    def _watch_clipboard(self):
        while self._running:
            try:
                clipboard_content = pyperclip.paste()
                if clipboard_content != self._last_clipboard:
                    self._last_clipboard = clipboard_content
                    url = self._extract_trusted_job_url(clipboard_content)
                    if url:
                        self.url_detected.emit(url)
            except Exception as e:
                logging.warning(f'Clipboard watchdog error: {e}')
            time.sleep(self.poll_interval)

    def _extract_trusted_job_url(self, text):
        try:
            parsed = urlparse(text.strip())
            if parsed.scheme in ('http', 'https') and parsed.netloc:
                for domain in TRUSTED_JOB_DOMAINS:
                    if domain in parsed.netloc:
                        return text.strip()
        except Exception:
            pass
        return None

