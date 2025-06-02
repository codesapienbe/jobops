"""
AI Motivation Letter Generator for Job Applications
"""

import logging
import threading
from typing import Optional, Literal
from pathlib import Path
from typing_extensions import Protocol
import webbrowser
import concurrent.futures
import asyncio

import psutil
from plyer import notification
import pystray
from PIL import Image, ImageDraw
from dotenv import load_dotenv
import pdfplumber


from jobops.clients import LLMBackendFactory
from jobops.models import Document, DocumentType, Resume
from jobops.config import CONSTANTS, JSONConfigManager
from jobops.repositories import SQLiteDocumentRepository
from jobops.scrapers import Crawl4AIJobScraper
from jobops.utils import DocumentExtractor, ConcreteLetterGenerator

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn


load_dotenv()

class NotificationService(Protocol):
    def notify(self, title: str, message: str) -> None: ...

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
        self._stop_event = threading.Event()
        self._threads = []
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
        timeout = self.config.sqlite_timeout if hasattr(self.config, 'sqlite_timeout') else 30.0
        self.repository = SQLiteDocumentRepository(str(db_path), timeout=timeout)
        backend_settings = self.config.backend_settings[self.config.backend]
        tokens = self.config.app_settings.get('tokens', {})
        self.llm_backend = LLMBackendFactory.create(self.config.backend, backend_settings, tokens)

        # Ensure Playwright browsers are installed if using Crawl4AI
        try:
            from playwright.sync_api import sync_playwright
            import shutil
            import subprocess
            import os

            logging.info("Playwright browsers not found. Installing browsers, this may take a few minutes...")
            try:
                self.notification_service.notify(
                    "JobOps",
                    "Installing Playwright browsers. This may take a few minutes on first run."
                )
            except Exception:
                pass
            subprocess.run(["playwright", "install"], check=True)
            # Try launching a browser to see if it works
            with sync_playwright() as p:
                try:
                    browser = p.chromium.launch(headless=True)
                    browser.close()
                except Exception:
                    self.notification_service.notify(
                        "JobOps",
                        "Playwright browsers not found. Please install them manually."
                    )
                    
        except ImportError:
            pass
        except Exception as e:
            logging.warning(f"Could not verify or install Playwright browsers: {e}")
        self.job_scraper = Crawl4AIJobScraper(self.llm_backend)
      
        
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
            
            if file_path.suffix.lower() == '.pdf':
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

        # Place this variable at the top of run() so it is accessible
        global_icon = None

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
                self._threads.append(anim_thread)
                try:
                    if self._stop_event.is_set():
                        return
                    doc = self.upload_document(file_path, DocumentType.RESUME)
                    if self._stop_event.is_set():
                        return
                    root.after(0, lambda: messagebox.showinfo("Success", f"Resume uploaded: {doc.filename}"))
                except Exception as e:
                    root.after(0, lambda e=e: messagebox.showerror("Error", f"Error uploading resume: {e}"))
                finally:
                    animating = False
                    root.after(0, root.destroy)

            root = tk.Tk()
            root.withdraw()
            root.after(0, ask_and_upload)
            root.mainloop()

        def on_generate_letter(icon, item):
            if icon is None:
                # Use the global icon if not provided (e.g., hotkey)
                nonlocal global_icon
                icon = global_icon
            import tkinter as tk
            from tkinter import messagebox
            import threading
            import os
            import time
            from pathlib import Path
            import json

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
            def animate_icon(icon):
                flip = False
                while animating:
                    icon.icon = img1 if flip else img2
                    flip = not flip
                    time.sleep(0.3)
                icon.icon = img1  # restore original

            def do_generate(job_url, job_data=None):
                self._logger.info("Starting motivation letter generation...")
                nonlocal animating
                nonlocal global_icon
                icon_to_animate = icon if icon is not None else global_icon
                anim_thread = threading.Thread(target=animate_icon, args=(icon_to_animate,), daemon=True)
                animating = True
                anim_thread.start()
                self._threads.append(anim_thread)
                watchdog_triggered = threading.Event()
                def watchdog():
                    import time
                    time.sleep(30)
                    if not watchdog_triggered.is_set():
                        self._logger.warning("Generation is taking too long. Triggering fallback and notifying user.")
                        try:
                            root.after(0, lambda: messagebox.showwarning("Timeout", "Generation is taking longer than expected. Using fallback extraction."))
                        except Exception:
                            pass
                        watchdog_triggered.set()
                watchdog_thread = threading.Thread(target=watchdog, daemon=True)
                watchdog_thread.start()
                self._threads.append(watchdog_thread)
                try:
                    if self._stop_event.is_set():
                        return
                    language = self.config.app_settings.get('language', 'en')
                    output_format = self.config.app_settings.get('output_format', 'pdf')
                    self._logger.info("Extracting job fields and preparing data...")
                    # Use provided job_data if available, otherwise scrape
                    fallback_used = False
                    if job_data is None and job_url:
                        try:
                            with concurrent.futures.ThreadPoolExecutor() as executor:
                                future = executor.submit(self.job_scraper.scrape_job_description, job_url)
                                try:
                                    job_data = future.result(timeout=25)
                                except concurrent.futures.TimeoutError:
                                    self._logger.warning("scrape_job_description timed out, using fallback.")
                                    fallback_used = True
                                    # Use fallback extraction
                                    markdown_content = ""
                                    try:
                                        markdown_content = asyncio.run(self.job_scraper._crawl_url(job_url))
                                    except Exception as e:
                                        self._logger.error(f"Crawl4AI fallback failed: {e}")
                                    job_data = self.job_scraper._fallback_extraction(job_url, markdown_content)
                        except Exception as e:
                            self._logger.error(f"Error in scrape_job_description: {e}")
                            fallback_used = True
                            markdown_content = ""
                            try:
                                markdown_content = asyncio.run(self.job_scraper._crawl_url(job_url))
                            except Exception as e:
                                self._logger.error(f"Crawl4AI fallback failed: {e}")
                            job_data = self.job_scraper._fallback_extraction(job_url, markdown_content)
                    if job_data:
                        self._logger.info("Generating motivation letter with LLM...")
                        try:
                            with concurrent.futures.ThreadPoolExecutor() as executor:
                                future = executor.submit(self.letter_generator.generate, job_data, Resume(summary=""), language)
                                try:
                                    result = future.result(timeout=25)
                                except concurrent.futures.TimeoutError:
                                    self._logger.warning("LLM generation timed out, using fallback scrape.")
                                    fallback_used = True
                                    # Use fallback extraction for job_data
                                    markdown_content = getattr(job_data, 'description', "")
                                    job_data = self.job_scraper._fallback_extraction(job_url, markdown_content)
                                    result = self.letter_generator.generate(job_data, Resume(summary=""), language)
                        except Exception as e:
                            self._logger.error(f"Error in LLM generation: {e}")
                            fallback_used = True
                            markdown_content = getattr(job_data, 'description', "")
                            job_data = self.job_scraper._fallback_extraction(job_url, markdown_content)
                            result = self.letter_generator.generate(job_data, Resume(summary=""), language)
                        import re
                        llm_response = result.content
                        think_match = re.search(r'<think>(.*?)</think>', llm_response, re.DOTALL | re.IGNORECASE)
                        reasoning_analysis = think_match.group(1).strip() if think_match else None
                        structured_content = re.sub(r'<think>.*?</think>', '', llm_response, flags=re.DOTALL | re.IGNORECASE).strip()
                        full_name = self.config.app_settings.get('personal_info', {}).get('name', '').strip() or ''
                        filename = f"{full_name} Cover Letter".strip() if full_name else "Cover Letter"
                        from datetime import datetime
                        from . import DocumentType, Document
                        self._logger.info("Saving generated document to database...")
                        document = Document(
                            type=DocumentType.COVER_LETTER,
                            filename=filename,
                            raw_content=result.content,
                            structured_content=structured_content,
                            reasoning_analysis=reasoning_analysis
                        )
                        self.repository.save(document)
                        self.notification_service.notify(
                            "JobOps", 
                            f"Motivation letter generated and stored in database."
                        )
                        if fallback_used:
                            try:
                                root.after(0, lambda: messagebox.showinfo("Fallback Used", "Fallback extraction was used due to timeout or error."))
                            except Exception:
                                pass
                    else:
                        self._logger.info("Falling back to generate_motivation_letter...")
                        result = self.generate_motivation_letter(job_url, language)
                    cover_letters = self.repository.get_by_type(DocumentType.COVER_LETTER)
                    cover_letters.sort(key=lambda d: d.uploaded_at, reverse=True)
                    latest_doc = cover_letters[0] if cover_letters else None
                    if latest_doc:
                        desktop = Path.home() / 'Desktop'
                        desktop.mkdir(exist_ok=True)
                        safe_filename = (latest_doc.filename or "Cover Letter").replace(os.sep, "_").replace(" ", "_")
                        pdf_path = desktop / f"{safe_filename}.pdf"
                        def export_pdf(markdown_content, pdf_filepath):
                            try:
                                from reportlab.lib.pagesizes import letter
                                from reportlab.pdfgen import canvas
                                from reportlab.lib.utils import simpleSplit
                                import markdown2
                                import re
                                html = markdown2.markdown(markdown_content)
                                text = re.sub('<[^<]+?>', '', html)
                                c = canvas.Canvas(str(pdf_filepath), pagesize=letter)
                                width, height = letter
                                margin = 40
                                y = height - margin
                                lines = simpleSplit(text, 'Helvetica', 12, width - 2*margin)
                                c.setFont("Helvetica", 12)
                                for line in lines:
                                    if y < margin:
                                        c.showPage()
                                        y = height - margin
                                        c.setFont("Helvetica", 12)
                                    c.drawString(margin, y, line)
                                    y -= 16
                                c.save()
                            except Exception:
                                try:
                                    from fpdf import FPDF
                                    pdf = FPDF()
                                    pdf.add_page()
                                    pdf.set_font("Arial", size=12)
                                    for line in markdown_content.split('\n'):
                                        pdf.cell(0, 10, txt=line, ln=1)
                                    pdf.output(str(pdf_filepath))
                                except Exception:
                                    messagebox.showerror("Error", "Could not export PDF. Please install reportlab or fpdf.")
                        export_pdf(latest_doc.structured_content, pdf_path)
                    def show_job_info_dialog(job_info, pdf_path):
                        win = tk.Toplevel()
                        win.title("Job/Company Info Summary")
                        win.geometry("520x420")
                        win.resizable(False, False)
                        frame = tk.Frame(win)
                        frame.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)
                        row = 0
                        def add_row(label, value):
                            nonlocal row
                            tk.Label(frame, text=label+":", anchor="w", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky="w", pady=2)
                            tk.Label(frame, text=value or "-", anchor="w", font=("Arial", 10)).grid(row=row, column=1, sticky="w", pady=2)
                            row += 1
                        add_row("URL", getattr(job_data, 'url', None) if job_data else None)
                        add_row("Title", getattr(job_data, 'title', None) if job_data else None)
                        add_row("Company", getattr(job_data, 'company', None) if job_data else None)
                        add_row("Location", getattr(job_data, 'location', None) if job_data else None)
                        add_row("Company Profile URL", getattr(job_data, 'company_profile_url', None) if job_data else None)
                        add_row("Company Profile", (getattr(job_data, 'company_profile', None) or "")[:200] + ("..." if getattr(job_data, 'company_profile', None) and len(getattr(job_data, 'company_profile', "")) > 200 else ""))
                        add_row("Salary", getattr(job_data, 'salary', None) if job_data else None)
                        add_row("Employment Type", getattr(job_data, 'employment_type', None) if job_data else None)
                        add_row("Seniority Level", getattr(job_data, 'seniority_level', None) if job_data else None)
                        add_row("Industry", getattr(job_data, 'industry', None) if job_data else None)
                        add_row("Company Size", getattr(job_data, 'company_size', None) if job_data else None)
                        add_row("Benefits", getattr(job_data, 'benefits', None) if job_data else None)
                        tk.Label(frame, text="\nPDF saved to:", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky="w", pady=8)
                        tk.Label(frame, text=str(pdf_path), font=("Arial", 10)).grid(row=row, column=1, sticky="w", pady=8)
                        row += 1
                        def copy_to_clipboard():
                            info_str = "\n".join(f"{k}: {v}" for k, v in job_info.items() if v)
                            info_str += f"\nPDF: {pdf_path}"
                            win.clipboard_clear()
                            win.clipboard_append(info_str)
                        btn = tk.Button(win, text="Copy Info to Clipboard", command=copy_to_clipboard)
                        btn.pack(pady=10)
                        tk.Button(win, text="Close", command=win.destroy).pack(pady=5)
                    job_info = None
                    if latest_doc and getattr(latest_doc, 'job_data_json', None):
                        try:
                            job_info = json.loads(latest_doc.job_data_json)
                        except Exception:
                            job_info = None
                    if job_info:
                        root.after(0, lambda: show_job_info_dialog(job_info, pdf_path))
                    elif job_data:
                        info = job_data
                        summary = f"""
Job Motivation Letter Generated!\n\nExtracted Job/Company Info:\n\n"""
                        summary += f"URL: {getattr(info, 'url', '')}\n"
                        summary += f"Title: {getattr(info, 'title', '')}\n"
                        summary += f"Company: {getattr(info, 'company', '')}\n"
                        if getattr(info, 'location', None):
                            summary += f"Location: {getattr(info, 'location', '')}\n"
                        if getattr(info, 'company_profile_url', None):
                            summary += f"Company Profile URL: {getattr(info, 'company_profile_url', '')}\n"
                        if getattr(info, 'company_profile', None):
                            summary += f"Company Profile: {getattr(info, 'company_profile', '')[:200]}...\n"
                        if getattr(info, 'salary', None):
                            summary += f"Salary: {getattr(info, 'salary', '')}\n"
                        if getattr(info, 'employment_type', None):
                            summary += f"Employment Type: {getattr(info, 'employment_type', '')}\n"
                        if getattr(info, 'seniority_level', None):
                            summary += f"Seniority Level: {getattr(info, 'seniority_level', '')}\n"
                        if getattr(info, 'industry', None):
                            summary += f"Industry: {getattr(info, 'industry', '')}\n"
                        if getattr(info, 'company_size', None):
                            summary += f"Company Size: {getattr(info, 'company_size', '')}\n"
                        if getattr(info, 'benefits', None):
                            summary += f"Benefits: {getattr(info, 'benefits', '')}\n"
                        summary += f"\nPDF saved to: {pdf_path}"
                        root.after(0, lambda: messagebox.showinfo("Success", summary))
                    else:
                        summary = f"Motivation letter generated and PDF saved to: {pdf_path}"
                        root.after(0, lambda: messagebox.showinfo("Success", summary))
                except Exception as e:
                    self._logger.error(f"Error generating letter: {e}")
                    try:
                        root.after(0, lambda e=e: messagebox.showerror("Error", f"Error generating letter: {e}"))
                    except Exception:
                        pass
                finally:
                    animating = False
                    watchdog_triggered.set()
                    root.after(0, root.destroy)

            # Single-entry dialog for job URL
            class JobInputDialog(tk.Toplevel):
                def __init__(self, master):
                    super().__init__(master)
                    self.title("Generate Motivation Letter")
                    self.geometry("600x340")
                    self.resizable(True, True)
                    import re
                    from urllib.parse import urlparse
                    self.mode = tk.StringVar(value="url")
                    placeholder_url = "Paste a valid job URL here (e.g. https://...)"
                    placeholder_text = "Paste the full job description text here..."
                    # Try to autofill from clipboard
                    try:
                        clipboard = master.clipboard_get()
                    except Exception:
                        clipboard = ""
                    # Heuristic: if clipboard looks like a URL, use it for URL mode
                    def is_url(text):
                        try:
                            parsed = urlparse(text)
                            return parsed.scheme in ("http", "https", "ftp", "ftps", "file")
                        except Exception:
                            return False
                    url_default = clipboard if is_url(clipboard) else ""
                    text_default = clipboard if (not url_default and len(clipboard) > 40) else ""
                    # --- UI ---
                    radio_frame = tk.Frame(self)
                    radio_frame.pack(pady=(18, 0))
                    tk.Radiobutton(radio_frame, text="Job URL", variable=self.mode, value="url", command=self.switch_mode).pack(side=tk.LEFT, padx=10)
                    tk.Radiobutton(radio_frame, text="Job Description Text", variable=self.mode, value="text", command=self.switch_mode).pack(side=tk.LEFT, padx=10)
                    # URL input
                    self.url_var = tk.StringVar(value=url_default or placeholder_url)
                    self.url_entry = tk.Entry(self, textvariable=self.url_var, width=60, fg='black' if url_default else 'grey')
                    self.url_entry.pack(pady=(10, 0))
                    # Text input (multi-line, always editable)
                    self.text_label = tk.Label(self, text="Paste the full job description text below:")
                    self.text_widget = tk.Text(self, width=70, height=10, wrap=tk.WORD)
                    if text_default:
                        self.text_widget.insert("1.0", text_default)
                    # Clipboard paste support (Ctrl+V and right-click)
                    def paste_clipboard(event=None):
                        try:
                            clipboard = self.clipboard_get()
                            self.text_widget.insert(tk.INSERT, clipboard)
                        except Exception:
                            pass
                        return "break"
                    self.text_widget.bind("<Control-v>", paste_clipboard)
                    self.text_widget.bind("<Control-V>", paste_clipboard)
                    # Right-click menu for paste
                    def show_context_menu(event):
                        menu = tk.Menu(self, tearoff=0)
                        menu.add_command(label="Paste", command=paste_clipboard)
                        menu.tk_popup(event.x_root, event.y_root)
                    self.text_widget.bind("<Button-3>", show_context_menu)
                    # Remove placeholder logic for text_widget
                    def url_focus_in(event):
                        if self.url_var.get() == placeholder_url:
                            self.url_var.set("")
                            self.url_entry.config(fg='black')
                    def url_focus_out(event):
                        if not self.url_var.get():
                            self.url_var.set(placeholder_url)
                            self.url_entry.config(fg='grey')
                        else:
                            self.url_entry.config(fg='black')
                    self.url_entry.bind('<FocusIn>', url_focus_in)
                    self.url_entry.bind('<FocusOut>', url_focus_out)
                    # --- Job fields (Company, Title, Location, Contact Person) ---
                    fields_frame = tk.Frame(self)
                    fields_frame.pack(pady=(8, 0), fill=tk.X)
                    tk.Label(fields_frame, text="Company Name:").grid(row=0, column=0, sticky="e", padx=5, pady=2)
                    tk.Label(fields_frame, text="Job Title:").grid(row=1, column=0, sticky="e", padx=5, pady=2)
                    tk.Label(fields_frame, text="Location:").grid(row=2, column=0, sticky="e", padx=5, pady=2)
                    tk.Label(fields_frame, text="Contact Person:").grid(row=3, column=0, sticky="e", padx=5, pady=2)
                    self.company_var = tk.StringVar()
                    self.title_var = tk.StringVar()
                    self.location_var = tk.StringVar()
                    self.contact_var = tk.StringVar()
                    tk.Entry(fields_frame, textvariable=self.company_var, width=40).grid(row=0, column=1, padx=5, pady=2)
                    tk.Entry(fields_frame, textvariable=self.title_var, width=40).grid(row=1, column=1, padx=5, pady=2)
                    tk.Entry(fields_frame, textvariable=self.location_var, width=40).grid(row=2, column=1, padx=5, pady=2)
                    tk.Entry(fields_frame, textvariable=self.contact_var, width=40).grid(row=3, column=1, padx=5, pady=2)
                    # Buttons
                    btn_frame = tk.Frame(self)
                    btn_frame.pack(pady=12)
                    btn_generate = tk.Button(btn_frame, text="Generate", command=self.on_generate)
                    btn_generate.pack(side=tk.LEFT, padx=10)
                    btn_cancel = tk.Button(btn_frame, text="Cancel", command=self.on_cancel)
                    btn_cancel.pack(side=tk.LEFT, padx=10)
                    self.protocol("WM_DELETE_WINDOW", self.on_cancel)
                    self.bind_all('<Escape>', lambda event: self.on_cancel())
                    self.url_entry.bind('<Return>', lambda event: self.on_generate())
                    self.switch_mode()
                    self.url_entry.focus_set()
                    self.master = master
                    # Always bring dialog to front and grab focus
                    self.lift()
                    self.attributes('-topmost', True)
                    self.focus_force()
                    self.grab_set()
                    self.after(200, lambda: self.attributes('-topmost', False))
                    # Clipboard watcher for URL auto-fill
                    self._last_clipboard = None
                    self._clipboard_polling = True
                    def poll_clipboard():
                        if not self._clipboard_polling:
                            return
                        try:
                            clipboard = self.clipboard_get()
                            from urllib.parse import urlparse
                            def is_url(text):
                                try:
                                    parsed = urlparse(text)
                                    return parsed.scheme in ("http", "https", "ftp", "ftps", "file")
                                except Exception:
                                    return False
                            if self.mode.get() == "url" and is_url(clipboard):
                                if (self.url_var.get() == placeholder_url or not self.url_var.get() or self.url_var.get() == self._last_clipboard):
                                    self.url_var.set(clipboard)
                                    self.url_entry.config(fg='black')
                                self._last_clipboard = clipboard
                        except Exception:
                            pass
                        self.after(500, poll_clipboard)
                    poll_clipboard()
                def switch_mode(self):
                    if self.mode.get() == "url":
                        self.url_entry.pack(pady=(10, 0))
                        self.text_label.pack_forget()
                        self.text_widget.pack_forget()
                        self.url_entry.focus_set()
                    else:
                        self.url_entry.pack_forget()
                        self.text_label.pack(pady=(10, 0))
                        self.text_widget.pack(pady=(0, 0), fill=tk.BOTH, expand=True)
                        self.text_widget.focus_set()
                def on_generate(self):
                    mode = self.mode.get()
                    if mode == "url":
                        url = self.url_var.get().strip()
                        if url == "Paste a valid job URL here (e.g. https://...)":
                            url = ""
                        if not url:
                            from tkinter import messagebox
                            messagebox.showerror("Error", "Please enter a job URL.")
                            return
                        # Crawl4AI: fetch job description from URL
                        job_data = None
                        try:
                            job_data = self.master.job_scraper.scrape_job_description(url)
                        except Exception as e:
                            job_data = None
                        job_text = job_data.description if job_data and hasattr(job_data, 'description') else ""
                        # Auto-fill fields if possible
                        if job_data:
                            self.company_var.set(getattr(job_data, 'company', '') or '')
                            self.title_var.set(getattr(job_data, 'title', '') or '')
                            self.location_var.set(getattr(job_data, 'location', '') or '')
                            self.contact_var.set(getattr(job_data, 'contact_info', '') or '')
                    else:
                        job_text = self.text_widget.get("1.0", tk.END).strip()
                        if job_text == "Paste the full job description text here...":
                            job_text = ""
                        if not job_text:
                            from tkinter import messagebox
                            messagebox.showerror("Error", "Please paste the job description text.")
                            return
                        url = None
                        # Extract and auto-fill fields from pasted text
                        extracted = self.extract_job_fields(job_text)
                        self.company_var.set(extracted.get('company', ''))
                        self.title_var.set(extracted.get('title', ''))
                        self.location_var.set(extracted.get('location', ''))
                        self.contact_var.set(extracted.get('contact_info', ''))
                    # Always use the current values from the entry fields
                    job_data = type('JobData', (object,), {
                        'company': self.company_var.get(),
                        'title': self.title_var.get(),
                        'location': self.location_var.get(),
                        'contact_info': self.contact_var.get(),
                        'description': job_text,
                        'url': url
                    })()
                    self.destroy()
                    threading.Thread(target=do_generate, args=(url, job_data), daemon=True).start()
                def extract_job_fields(self, text):
                    # Try LLM extraction if available, fallback to regex
                    try:
                        llm = self.master.llm_backend
                        prompt = f"""
Extract the following fields from the job description below. Return as JSON with keys: company, title, location, contact_info. If not found, use empty string.

Job Description:
{text}
"""
                        import json
                        response = llm.generate_response(prompt, system_prompt="You are an expert at extracting job fields from unstructured text. Return only valid JSON.")
                        data = json.loads(response)
                        return {
                            'company': data.get('company', ''),
                            'title': data.get('title', ''),
                            'location': data.get('location', ''),
                            'contact_info': data.get('contact_info', '')
                        }
                    except Exception:
                        # Fallback regex extraction
                        import re
                        company = ""
                        title = ""
                        location = ""
                        contact_info = ""
                        # Simple regex patterns (can be improved)
                        company_match = re.search(r'Company[:\s]+(.+)', text, re.IGNORECASE)
                        if company_match:
                            company = company_match.group(1).split('\n')[0].strip()
                        title_match = re.search(r'(Job Title|Position)[:\s]+(.+)', text, re.IGNORECASE)
                        if title_match:
                            title = title_match.group(2).split('\n')[0].strip()
                        location_match = re.search(r'Location[:\s]+(.+)', text, re.IGNORECASE)
                        if location_match:
                            location = location_match.group(1).split('\n')[0].strip()
                        contact_match = re.search(r'Contact[:\s]+(.+)', text, re.IGNORECASE)
                        if contact_match:
                            contact_info = contact_match.group(1).split('\n')[0].strip()
                        return {
                            'company': company,
                            'title': title,
                            'location': location,
                            'contact_info': contact_info
                        }
                def on_cancel(self):
                    # Prevent multiple calls
                    if hasattr(self, '_cancelled') and self._cancelled:
                        return
                    self._cancelled = True
                    self._clipboard_polling = False
                    try:
                        self.grab_release()
                    except Exception:
                        pass
                    self.destroy()

            root = tk.Tk()
            root.withdraw()
            JobInputDialog(root)
            root.mainloop()

        def on_download_cover_letter(icon, item):
            import tkinter as tk
            from tkinter import simpledialog, filedialog, messagebox
            import threading
            import datetime
            import os
            # Helper for PDF export
            def export_pdf(markdown_content, pdf_filepath):
                try:
                    from reportlab.lib.pagesizes import letter
                    from reportlab.pdfgen import canvas
                    from reportlab.lib.utils import simpleSplit
                    import markdown2
                    import re
                    html = markdown2.markdown(markdown_content)
                    text = re.sub('<[^<]+?>', '', html)
                    c = canvas.Canvas(str(pdf_filepath), pagesize=letter)
                    width, height = letter
                    margin = 40
                    y = height - margin
                    lines = simpleSplit(text, 'Helvetica', 12, width - 2*margin)
                    c.setFont("Helvetica", 12)
                    for line in lines:
                        if y < margin:
                            c.showPage()
                            y = height - margin
                            c.setFont("Helvetica", 12)
                        c.drawString(margin, y, line)
                        y -= 16
                    c.save()
                except Exception:
                    try:
                        from fpdf import FPDF
                        pdf = FPDF()
                        pdf.add_page()
                        pdf.set_font("Arial", size=12)
                        for line in markdown_content.split('\n'):
                            pdf.cell(0, 10, txt=line, ln=1)
                        pdf.output(str(pdf_filepath))
                    except Exception:
                        messagebox.showerror("Error", "Could not export PDF. Please install reportlab or fpdf.")
            # Dialog for selecting cover letter and format
            class DownloadDialog(tk.Toplevel):
                def __init__(self, master, cover_letters):
                    super().__init__(master)
                    self.title("Download")
                    self.geometry("500x350")
                    self.cover_letters = cover_letters
                    self.selected_idx = tk.IntVar(value=0)
                    self.format_var = tk.StringVar(value="markdown")
                    self.build_ui()
                def build_ui(self):
                    tk.Label(self, text="Select a cover letter to download:", font=("Arial", 12)).pack(pady=10)
                    self.listbox = tk.Listbox(self, width=60, height=10)
                    for i, doc in enumerate(self.cover_letters):
                        dt = doc.uploaded_at.strftime('%Y-%m-%d %H:%M') if hasattr(doc, 'uploaded_at') else ''
                        name = doc.filename or f"Cover Letter {i+1}"
                        self.listbox.insert(tk.END, f"{name} ({dt})")
                    self.listbox.pack(pady=5)
                    self.listbox.select_set(0)
                    tk.Label(self, text="Format:").pack(pady=(10,0))
                    format_frame = tk.Frame(self)
                    format_frame.pack()
                    tk.Radiobutton(format_frame, text="Markdown", variable=self.format_var, value="markdown").pack(side=tk.LEFT, padx=10)
                    tk.Radiobutton(format_frame, text="PDF", variable=self.format_var, value="pdf").pack(side=tk.LEFT, padx=10)
                    btn_frame = tk.Frame(self)
                    btn_frame.pack(pady=15)
                    tk.Button(btn_frame, text="Download", command=self.on_download).pack(side=tk.LEFT, padx=10)
                    tk.Button(btn_frame, text="Cancel", command=self.destroy).pack(side=tk.LEFT, padx=10)
                def on_download(self):
                    idx = self.listbox.curselection()
                    if not idx:
                        messagebox.showerror("Error", "Please select a cover letter.")
                        return
                    doc = self.cover_letters[idx[0]]
                    fmt = self.format_var.get()
                    ext = ".md" if fmt == "markdown" else ".pdf"
                    default_name = (doc.filename or "Cover Letter") + ext
                    file_path = filedialog.asksaveasfilename(defaultextension=ext, initialfile=default_name, filetypes=[("Markdown", "*.md"), ("PDF", "*.pdf"), ("All Files", "*.*")])
                    if not file_path:
                        return
                    try:
                        if fmt == "markdown":
                            with open(file_path, 'w', encoding='utf-8') as f:
                                f.write(doc.structured_content)
                        else:
                            export_pdf(doc.structured_content, file_path)
                        messagebox.showinfo("Success", f"Cover letter saved to {os.path.basename(file_path)}")
                        self.destroy()
                    except Exception as e:
                        messagebox.showerror("Error", f"Failed to save file: {e}")
            def show_download_dialog():
                if self._stop_event.is_set():
                    return
                root = tk.Tk()
                root.withdraw()
                # Fetch all cover letters from the DB
                cover_letters = self.repository.get_by_type(DocumentType.COVER_LETTER)
                if not cover_letters:
                    messagebox.showinfo("No Cover Letters", "No cover letters found in the database.")
                    root.destroy()
                    return
                DownloadDialog(root, cover_letters)
                root.mainloop()
            t = threading.Thread(target=show_download_dialog, daemon=True)
            self._threads.append(t)
            t.start()

        def on_change_backend(icon, item):
            import tkinter as tk
            from tkinter import messagebox
            import threading

            def show_backend_dialog():
                root = tk.Tk()
                root.withdraw()
                backends = list(self.config.backend_settings.keys())
                current_backend = self.config.backend

                class BackendDialog(tk.Toplevel):
                    def __init__(self, master, app_self):
                        super().__init__(master)
                        self.app_self = app_self
                        self.title("Backend")
                        self.geometry("350x200")
                        self.resizable(False, False)
                        self.selected_backend = tk.StringVar(value=current_backend)
                        self.build_ui()

                    def build_ui(self):
                        tk.Label(self, text="Select Backend:", font=("Arial", 12)).pack(pady=15)
                        for backend in backends:
                            tk.Radiobutton(self, text=backend.capitalize(), variable=self.selected_backend, value=backend).pack(anchor=tk.W, padx=30)
                        btn_frame = tk.Frame(self)
                        btn_frame.pack(pady=20)
                        tk.Button(btn_frame, text="Save", command=self.on_save).pack(side=tk.LEFT, padx=10)
                        tk.Button(btn_frame, text="Cancel", command=self.destroy).pack(side=tk.LEFT, padx=10)

                    def on_save(self):
                        new_backend = self.selected_backend.get()
                        if new_backend != self.app_self.config.backend:
                            self.app_self.config.backend = new_backend
                            self.app_self.config_manager.save(self.app_self.config)
                            # Re-initialize services
                            backend_settings = self.app_self.config.backend_settings[self.app_self.config.backend]
                            tokens = self.app_self.config.app_settings.get('tokens', {})
                            self.app_self.llm_backend = LLMBackendFactory.create(self.app_self.config.backend, backend_settings, tokens)
                            self.app_self.job_scraper = Crawl4AIJobScraper(self.app_self.llm_backend)
                            self.app_self.letter_generator = ConcreteLetterGenerator(self.app_self.llm_backend)
                            self.app_self.document_extractor = DocumentExtractor(self.app_self.llm_backend)
                            self.app_self.notification_service.notify("JobOps", f"Backend changed to {new_backend}.")
                            messagebox.showinfo("Backend", f"Backend changed to {new_backend}.")
                        self.destroy()

                BackendDialog(root, self)
                root.mainloop()

            t = threading.Thread(target=show_backend_dialog, daemon=True)
            self._threads.append(t)
            t.start()

        def on_settings(icon, item):
            import tkinter as tk
            from tkinter import simpledialog, messagebox
            import threading

            def show_settings_dialog():
                root = tk.Tk()
                root.withdraw()
                # Get current tokens from config
                tokens = self.config.app_settings.get('tokens', {})
                openai_token = tokens.get('openai', '')
                groq_token = tokens.get('groq', '')
                # Add more providers as needed

                class SettingsDialog(tk.Toplevel):
                    def __init__(self, master):
                        super().__init__(master)
                        self.title("API Tokens Settings")
                        self.geometry("400x250")
                        self.resizable(False, False)
                        self.openai_var = tk.StringVar(value=openai_token)
                        self.groq_var = tk.StringVar(value=groq_token)
                        self.build_ui()

                    def build_ui(self):
                        row = 0
                        tk.Label(self, text="OpenAI API Key:").grid(row=row, column=0, sticky="e", padx=10, pady=10)
                        tk.Entry(self, textvariable=self.openai_var, width=40, show="*").grid(row=row, column=1, padx=10, pady=10)
                        row += 1
                        tk.Label(self, text="Groq API Key:").grid(row=row, column=0, sticky="e", padx=10, pady=10)
                        tk.Entry(self, textvariable=self.groq_var, width=40, show="*").grid(row=row, column=1, padx=10, pady=10)
                        row += 1
                        # Add more providers here as needed
                        btn_frame = tk.Frame(self)
                        btn_frame.grid(row=row, column=0, columnspan=2, pady=20)
                        tk.Button(btn_frame, text="Save", command=self.on_save).pack(side=tk.LEFT, padx=10)
                        tk.Button(btn_frame, text="Cancel", command=self.destroy).pack(side=tk.LEFT, padx=10)

                    def on_save(self):
                        # Save tokens to config
                        new_tokens = {
                            'openai': self.openai_var.get().strip(),
                            'groq': self.groq_var.get().strip(),
                            'gemini': self.gemini_var.get().strip(),
                            'xgrok': self.xgrok_var.get().strip(),
                            'perplexity': self.perplexity_var.get().strip(),
                        }
                        self.master.after(0, lambda: self.save_tokens(new_tokens))
                        self.destroy()

                    def save_tokens(self, new_tokens):
                        self.master.withdraw()  # Hide the root window
                        self.master.update()
                        self.master.destroy()
                        self._save_tokens(new_tokens)

                    def _save_tokens(self, new_tokens):
                        self = self  # for clarity
                        # Update config and save
                        self_ref = self  # for closure
                        try:
                            self_ref = self
                            self_ref = None  # silence linter
                        except Exception:
                            pass
                        self_ = self  # for closure
                        # Actually update config
                        self_ = None  # silence linter
                        # Save tokens
                        self_ = None
                        # Actually update config
                        self.config.app_settings['tokens'] = new_tokens
                        self.config_manager.save(self.config)
                        self.notification_service.notify("JobOps", "API tokens saved.")
                        messagebox.showinfo("Settings", "API tokens saved successfully.")

                SettingsDialog(root)
                root.mainloop()

            t = threading.Thread(target=show_settings_dialog, daemon=True)
            self._threads.append(t)
            t.start()

        def on_exit(icon, item):
            print("Exiting application. Goodbye!")
            try:
                self.notification_service.notify("JobOps", "Exiting application. Goodbye!")
                self._stop_event.set()
                # Wait for all background threads to finish (with timeout)
                for thread in self._threads:
                    if thread.is_alive():
                        thread.join(timeout=5)
                # KILL ALL PROCESSES belongs to this application
                for process in psutil.process_iter():
                    if process.name() == "jobops.exe":
                        process.kill()
            except Exception as e:
                logging.error(f"Error notifying: {e}")
            icon.stop()

        def on_help_github_repo(icon, item):
            webbrowser.open("https://github.com/codesapienbe/jobops-toolbar")

        menu = pystray.Menu(
            pystray.MenuItem("Upload", on_upload_resume),
            pystray.MenuItem("Generate", on_generate_letter),
            pystray.MenuItem("Download", on_download_cover_letter),
            pystray.MenuItem("Backend", on_change_backend),
            pystray.MenuItem("Settings", on_settings),
            pystray.MenuItem("Help", on_help_github_repo),
            pystray.MenuItem("Exit", on_exit)
        )
        icon = pystray.Icon(CONSTANTS.APP_NAME, create_image(), CONSTANTS.APP_NAME, menu)
        global_icon = icon
        icon.run()

        # Global hotkey: Ctrl+Alt+J to open the motivation letter wizard
        def start_hotkey_listener():
            try:
                from pynput import keyboard
            except ImportError:
                self._logger.warning("pynput not installed, global hotkey disabled.")
                return
            def on_activate():
                # Use the same logic as the tray menu's Generate action
                threading.Thread(target=lambda: on_generate_letter(None, None), daemon=True).start()
            COMBO = {keyboard.Key.ctrl_l, keyboard.Key.alt_l, keyboard.KeyCode.from_char('j')}
            current_keys = set()
            def on_press(key):
                if key in COMBO:
                    current_keys.add(key)
                if all(k in current_keys for k in COMBO):
                    on_activate()
            def on_release(key):
                if key in current_keys:
                    current_keys.remove(key)
            listener = keyboard.Listener(on_press=on_press, on_release=on_release)
            listener.daemon = True
            listener.start()
            self._threads.append(listener)
        start_hotkey_listener()

# --- FastAPI setup ---
app_fastapi = FastAPI()

class LLMRequest(BaseModel):
    prompt: str
    system_prompt: Optional[str] = None
    backend: Literal["ollama", "openai", "groq"]

class LLMResponse(BaseModel):
    response: str

# Use your config loading here
BACKEND_SETTINGS = {
    "ollama": {"model": "qwen3:0.6b", "base_url": "http://localhost:11434"},
    "openai": {"model": "gpt-4-turbo-preview"},
    "groq": {"model": "mixtral-8x7b-32768"},
}
TOKENS = {
    "openai": "YOUR_OPENAI_API_KEY",
    "groq": "YOUR_GROQ_API_KEY",
}

@app_fastapi.post("/llm", response_model=LLMResponse)
def llm_proxy(req: LLMRequest):
    try:
        backend = LLMBackendFactory.create(
            req.backend,
            BACKEND_SETTINGS[req.backend],
            TOKENS
        )
        result = backend.generate_response(req.prompt, req.system_prompt)
        return LLMResponse(response=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app_fastapi.get("/health/{backend}")
def healthcheck(backend: Literal["ollama", "openai", "groq"]):
    try:
        backend_obj = LLMBackendFactory.create(
            backend,
            BACKEND_SETTINGS[backend],
            TOKENS
        )
        healthy = backend_obj.health_check()
        return JSONResponse({"status": "ok" if healthy else "unhealthy"})
    except Exception as e:
        return JSONResponse({"status": "unhealthy", "error": str(e)}, status_code=500)

def start_fastapi():
    uvicorn.run(app_fastapi, host="0.0.0.0", port=8000, log_level="info")

def main():
    try:
        # Start FastAPI in a background thread
        threading.Thread(target=start_fastapi, daemon=True).start()
        app = JobOpsApplication()
        app.run()
    except KeyboardInterrupt:
        logging.info("Application interrupted by user")
    except Exception as e:
        logging.error(f"Application error: {e}")
        # --- Error reporting dialog ---
        try:
            import tkinter as tk
            from tkinter import messagebox
            import webbrowser
            import urllib.parse
            # Load user profile info
            config_path = Path.home() / ".jobops" / "config.json"
            import json
            if config_path.exists():
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                profile = config.get("app_settings", {}).get("personal_info", {})
            else:
                profile = {}
            profile_str = "\n".join(f"{k}: {v}" for k, v in profile.items())
            # Get last 100 lines of log
            log_path = Path.home() / ".jobops" / "app.log"
            if log_path.exists():
                with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()
                log_tail = "".join(lines[-100:])
            else:
                log_tail = "(log file not found)"
            # Compose email body
            body = f"""An error occurred in JobOps.\n\nError message:\n{e}\n\nUser profile:\n{profile_str}\n\nLast 100 lines of log:\n{log_tail}\n\nPlease attach the full app.log file if possible.\n"""
            body = urllib.parse.quote(body)
            subject = urllib.parse.quote("JobOps Error Report")
            mailto = f"mailto:ymus@tuta.io?subject={subject}&body={body}"
            # Show dialog
            root = tk.Tk()
            root.withdraw()
            if messagebox.askyesno("JobOps Error", "An unexpected error occurred. Would you like to report this to the developers? This will open your email client with the error details. Please attach the log file if possible."):
                webbrowser.open(mailto)
            root.destroy()
        except Exception as ee:
            logging.error(f"Error in error reporting dialog: {ee}")
        raise
    finally:
        logging.info("Application ended")

if __name__ == "__main__":
    main()
