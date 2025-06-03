import sys
import os
import logging
import base64
import tempfile
from pathlib import Path
import webbrowser
from PIL import Image
from io import BytesIO
from PySide6.QtCore import Signal
import json
from fpdf import FPDF
from jobops.utils import export_letter_to_pdf, extract_reasoning_analysis, clean_job_data_dict, ResourceManager, NotificationService, check_platform_compatibility, create_desktop_entry, ClipboardJobUrlWatchdog

# Qt imports
try:
    from PySide6.QtWidgets import *
    from PySide6.QtCore import *
    from PySide6.QtGui import *
    QT_AVAILABLE = True
except ImportError:
    try:
        from PyQt6.QtWidgets import *
        from PyQt6.QtCore import *
        from PyQt6.QtGui import *
        QT_AVAILABLE = True
    except ImportError:
        QT_AVAILABLE = False
        print("Neither PySide6 nor PyQt6 is installed. Please install one of them.")
        sys.exit(1)


from dotenv import load_dotenv
from jobops.models import DocumentType, Document

# Embedded base64 icon data (64x64 PNG icon)
EMBEDDED_ICON_DATA = """
iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAYAAACqaXHeAAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAOxAAADsQBlSsOGwAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAAOxSURBVHic7ZtNaBNBFMefJFqrtVZbW6u01lq1Wq21aq3VWmut1lqrtdZqrdVaq7VWa63VWqu1VmuttVprtdZqrdVaq7VWa63VWqu1VmuttVprtdZqrdVaq7VWa63VWqu1VmuttVprtdZqrdVaq7VWa63VWqu1VmuttVprtdZqrdVaq7VWa60AAAD//2Q=="
"""

try:
    icon_data = base64.b64decode(EMBEDDED_ICON_DATA)
    img = Image.open(BytesIO(icon_data))
    img.show()
except Exception as e:
    print("Failed to load image:", e)

load_dotenv()

class JobInputDialog(QDialog):
    """Modern job input dialog"""
    job_data_ready = Signal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Generate Motivation Letter")
        self.setFixedSize(650, 500)
        self.setWindowIcon(ResourceManager.create_app_icon())
        
        self.job_data = None
        self.setup_ui()
        # Clipboard watchdog for job URLs
        self.clipboard_watchdog = ClipboardJobUrlWatchdog(self)
        self.clipboard_watchdog.url_detected.connect(self.on_trusted_job_url_detected)
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Mode selection
        mode_group = QGroupBox("Input Method")
        mode_layout = QHBoxLayout(mode_group)
        
        self.url_radio = QRadioButton("Job URL")
        self.text_radio = QRadioButton("Job Description Text")
        self.url_radio.setChecked(True)
        
        mode_layout.addWidget(self.url_radio)
        mode_layout.addWidget(self.text_radio)
        layout.addWidget(mode_group)
        
        # Input stack
        self.input_stack = QStackedWidget()
        
        # URL input page
        url_page = QWidget()
        url_layout = QVBoxLayout(url_page)
        url_layout.addWidget(QLabel("Job URL:"))
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://...")
        url_layout.addWidget(self.url_input)
        self.input_stack.addWidget(url_page)
        
        # Text input page
        text_page = QWidget()
        text_layout = QVBoxLayout(text_page)
        text_layout.addWidget(QLabel("Paste the full job description:"))
        self.text_input = QTextEdit()
        self.text_input.setPlaceholderText("Paste job description here...")
        text_layout.addWidget(self.text_input)
        self.input_stack.addWidget(text_page)
        
        layout.addWidget(self.input_stack)
        
        # Job details
        details_group = QGroupBox("Job Details (Optional)")
        details_layout = QFormLayout(details_group)
        
        self.company_input = QLineEdit()
        self.title_input = QLineEdit()
        self.location_input = QLineEdit()
        self.contact_input = QLineEdit()
        self.requirements_input = QTextEdit()
        self.requirements_input.setPlaceholderText("Paste job requirements here...")
        
        details_layout.addRow("Company Name:", self.company_input)
        details_layout.addRow("Job Title:", self.title_input)
        details_layout.addRow("Location:", self.location_input)
        details_layout.addRow("Contact Person:", self.contact_input)
        details_layout.addRow("Requirements:", self.requirements_input)
        
        layout.addWidget(details_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.generate_btn = QPushButton("Generate Letter")
        self.cancel_btn = QPushButton("Cancel")
        
        self.generate_btn.clicked.connect(self.generate_letter)
        self.cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(self.generate_btn)
        button_layout.addWidget(self.cancel_btn)
        layout.addLayout(button_layout)
        
        # Connect radio buttons
        self.url_radio.toggled.connect(self.on_mode_changed)
        self.text_radio.toggled.connect(self.on_mode_changed)
    
    def on_mode_changed(self):
        if self.url_radio.isChecked():
            self.input_stack.setCurrentIndex(0)
        else:
            self.input_stack.setCurrentIndex(1)
    
    def generate_letter(self):
        if self.url_radio.isChecked():
            url = self.url_input.text().strip()
            if not url:
                QMessageBox.warning(self, "Error", "Please enter a job URL.")
                return
            job_text = ""
        else:
            job_text = self.text_input.toPlainText().strip()
            if not job_text:
                QMessageBox.warning(self, "Error", "Please paste the job description.")
                return
            url = None
        
        # Create job data object
        self.job_data = {
            'url': url,
            'description': job_text,
            'company': self.company_input.text().strip(),
            'title': self.title_input.text().strip(),
            'requirements': self.requirements_input.toPlainText().strip(),
            'location': self.location_input.text().strip(),
            'contact_info': self.contact_input.text().strip()
        }
        self.job_data_ready.emit(self.job_data)
        self.accept()

    def showEvent(self, event):
        super().showEvent(event)
        self.clipboard_watchdog.start()

    def closeEvent(self, event):
        self.clipboard_watchdog.stop()
        if hasattr(self, 'generate_worker') and self.generate_worker.isRunning():
            self.generate_worker.wait()
        event.accept()

    def on_trusted_job_url_detected(self, url):
        self.url_input.setText(url)
        self.url_radio.setChecked(True)
        self.input_stack.setCurrentIndex(0)

class UploadDialog(QDialog):
    """File upload dialog"""
    upload_data_ready = Signal(str, str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Upload Document")
        self.setFixedSize(400, 200)
        self.setWindowIcon(ResourceManager.create_app_icon())
        
        self.file_path = None
        self.doc_type = None
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # File selection
        file_layout = QHBoxLayout()
        self.file_input = QLineEdit()
        self.file_input.setPlaceholderText("Select a file...")
        self.browse_btn = QPushButton("Browse")
        self.browse_btn.clicked.connect(self.browse_file)
        
        file_layout.addWidget(self.file_input)
        file_layout.addWidget(self.browse_btn)
        layout.addLayout(file_layout)
        
        # Document type
        type_group = QGroupBox("Document Type")
        type_layout = QVBoxLayout(type_group)
        
        self.resume_radio = QRadioButton("Resume/CV")
        self.cert_radio = QRadioButton("Certificate")
        self.resume_radio.setChecked(True)
        
        type_layout.addWidget(self.resume_radio)
        type_layout.addWidget(self.cert_radio)
        layout.addWidget(type_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.upload_btn = QPushButton("Upload")
        self.cancel_btn = QPushButton("Cancel")
        
        self.upload_btn.clicked.connect(self.upload_document)
        self.cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(self.upload_btn)
        button_layout.addWidget(self.cancel_btn)
        layout.addLayout(button_layout)
    
    def browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Select Document", 
            "", 
            "Documents (*.pdf *.txt *.doc *.docx);;All Files (*)"
        )
        if file_path:
            self.file_input.setText(file_path)
    
    def upload_document(self):
        file_path = self.file_input.text().strip()
        if not file_path:
            QMessageBox.warning(self, "Error", "Please select a file.")
            return
        
        if not os.path.exists(file_path):
            QMessageBox.warning(self, "Error", "File does not exist.")
            return
        
        self.file_path = file_path
        self.doc_type = "RESUME" if self.resume_radio.isChecked() else "CERTIFICATION"
        self.upload_data_ready.emit(self.file_path, self.doc_type)
        self.accept()

class SystemTrayIcon(QSystemTrayIcon):
    """Custom system tray icon with JobOps functionality"""
    
    def __init__(self, app_instance, parent=None):
        super().__init__(parent)
        self.app_instance = app_instance
        self.animation_timer = None
        self.animation_frames = self._create_animation_frames()
        self.animation_index = 0
        self.is_animating = False
        self.progress_dialog = None
        self.setup_tray()
    
    def _create_animation_frames(self):
        """Create a list of QIcons for animation (spinner effect)"""
        frames = []
        base_pixmap = ResourceManager.create_app_icon().pixmap(64, 64)
        for angle in range(0, 360, 30):
            pixmap = QPixmap(base_pixmap.size())
            pixmap.fill(Qt.GlobalColor.transparent)
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.translate(pixmap.width() / 2, pixmap.height() / 2)
            painter.rotate(angle)
            painter.translate(-pixmap.width() / 2, -pixmap.height() / 2)
            painter.drawPixmap(0, 0, base_pixmap)
            painter.end()
            frames.append(QIcon(pixmap))
        return frames if frames else [ResourceManager.create_app_icon()]

    def start_animation(self):
        if self.is_animating:
            return
        logging.info("Starting tray icon animation (generation in progress)")
        self.is_animating = True
        if not self.animation_timer:
            self.animation_timer = QTimer(self)
            self.animation_timer.timeout.connect(self._animate_icon)
        self.animation_index = 0
        self.animation_timer.start(100)  # 100ms per frame

    def stop_animation(self):
        if self.animation_timer:
            self.animation_timer.stop()
        self.setIcon(ResourceManager.create_app_icon())
        self.is_animating = False
        logging.info("Stopped tray icon animation (generation finished)")

    def _animate_icon(self):
        if not self.is_animating or not self.animation_frames:
            return
        self.setIcon(self.animation_frames[self.animation_index])
        self.animation_index = (self.animation_index + 1) % len(self.animation_frames)

    def setup_tray(self):
        # Set icon
        self.setIcon(ResourceManager.create_app_icon())
        self.setToolTip("JobOps - AI Motivation Letter Generator")
        
        # Create context menu
        menu = QMenu()
        
        # Add actions
        upload_action = QAction("📁 Upload Document", self)
        generate_action = QAction("✨ Generate Letter", self)
        download_action = QAction("💾 Download Letters", self)
        settings_action = QAction("⚙️ Settings", self)
        help_action = QAction("❓ Help", self)
        quit_action = QAction("❌ Exit", self)
        
        # Connect actions
        upload_action.triggered.connect(self.upload_document)
        generate_action.triggered.connect(self.generate_letter)
        download_action.triggered.connect(self.download_letters)
        settings_action.triggered.connect(self.show_settings)
        help_action.triggered.connect(self.show_help)
        quit_action.triggered.connect(self.quit_application)
        
        # Add to menu
        menu.addAction(upload_action)
        menu.addAction(generate_action)
        menu.addSeparator()
        menu.addAction(download_action)
        menu.addAction(settings_action)
        menu.addAction(help_action)
        menu.addSeparator()
        menu.addAction(quit_action)
        
        self.setContextMenu(menu)
        
        # Connect signals
        self.messageClicked.connect(self.on_message_clicked)
        self.activated.connect(self.on_tray_activated)
    
    def upload_document(self):
        logging.info("User triggered: Upload Document dialog")
        dialog = UploadDialog()
        dialog.upload_data_ready.connect(self._start_upload_worker)
        dialog.exec()
    
    def _start_upload_worker(self, file_path, doc_type):
        logging.info(f"Uploading document: {file_path} as {doc_type}")
        worker = UploadWorker(self.app_instance, file_path, doc_type)
        worker.finished.connect(self.on_upload_finished)
        worker.error.connect(self.on_upload_error)
        worker.start()
    
    def generate_letter(self):
        logging.info("User triggered: Generate Letter dialog")
        dialog = JobInputDialog()
        dialog.job_data_ready.connect(self._start_generate_worker)
        dialog.exec()
    
    def _start_generate_worker(self, job_data):
        logging.info(f"Starting letter generation for job data: {job_data}")
        self.generate_worker = GenerateWorker(self.app_instance, job_data)
        self.generate_worker.finished.connect(self.on_generation_finished)
        self.generate_worker.error.connect(self.on_generation_error)
        self.start_animation()
        # Show progress dialog
        self.progress_dialog = QProgressDialog("Generating motivation letter...", None, 0, 0)
        self.progress_dialog.setWindowTitle("JobOps")
        self.progress_dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.progress_dialog.setCancelButton(None)
        self.progress_dialog.setMinimumDuration(0)
        self.progress_dialog.show()
        # Show notification
        self.showMessage(
            "JobOps",
            "Generating your motivation letter...",
            QSystemTrayIcon.MessageIcon.Information,
            2000
        )
        self.generate_worker.start()
    
    def download_letters(self):
        logging.info("User triggered: Download Letters dialog")
        # Fetch all motivation letters (stored as COVER_LETTER)
        try:
            letters = self.app_instance.repository.get_by_type(DocumentType.COVER_LETTER)
            if not letters:
                QMessageBox.information(None, "Download", "No motivation letters found.")
                return
            # Ask user for directory
            dir_path = QFileDialog.getExistingDirectory(None, "Select Download Directory")
            if not dir_path:
                return
            count = 0
            for doc in letters:
                # Try to extract job title and date for filename
                job_title = "letter"
                job_data = None
                if hasattr(doc, 'job_data_json') and doc.job_data_json:
                    import json
                    try:
                        job_data = json.loads(doc.job_data_json)
                        if 'title' in job_data and job_data['title']:
                            job_title = job_data['title'].replace(' ', '_')
                    except Exception:
                        pass
                date_str = doc.uploaded_at.strftime('%Y%m%d_%H%M%S') if hasattr(doc, 'uploaded_at') else str(count)
                filename = f"{job_title}_{date_str}.md"
                filepath = os.path.join(dir_path, filename)
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(doc.structured_content or doc.raw_content or "")
                count += 1
            QMessageBox.information(None, "Download", f"Exported {count} motivation letters to {dir_path}")
        except Exception as e:
            logging.error(f"Error exporting motivation letters: {e}")
        # Implementation for downloading letters
        QMessageBox.information(None, "Download", "Download functionality will be implemented here.")
    
    def show_settings(self):
        logging.info("User triggered: Settings dialog")
        # Implementation for settings
        QMessageBox.information(None, "Settings", "Settings dialog will be implemented here.")
    
    def show_help(self):
        logging.info("User triggered: Help/documentation")
        webbrowser.open("https://github.com/codesapienbe/jobops-toolbar")
    
    def quit_application(self):
        logging.info("User triggered: Quit application")
        reply = QMessageBox.question(
            None, 
            "Exit JobOps", 
            "Are you sure you want to exit JobOps?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            QApplication.quit()
    
    def on_upload_finished(self, message):
        logging.info(f"Upload finished: {message}")
        self.showMessage("JobOps", message, QSystemTrayIcon.MessageIcon.Information, 3000)
    
    def on_upload_error(self, error):
        logging.error(f"Upload error: {error}")
        self.showMessage("JobOps Error", error, QSystemTrayIcon.MessageIcon.Critical, 5000)
    
    def on_generation_finished(self, message):
        logging.info("Letter generation finished successfully.")
        self.stop_animation()
        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None
        # Show tray notification
        self.showMessage("JobOps", message, QSystemTrayIcon.MessageIcon.Information, 5000)
        logging.info(f"Tray notification shown: {message}")
        # Fallback: use NotificationService if available
        if hasattr(self.app_instance, 'notification_service') and self.app_instance.notification_service:
            self.app_instance.notification_service.notify("JobOps", message)
            logging.info("Fallback notification service used.")
        # No dialog with letter content
    
    def on_generation_error(self, error):
        logging.error(f"Letter generation error: {error}")
        self.stop_animation()
        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None
        # Show tray notification
        self.showMessage("JobOps Error", error, QSystemTrayIcon.MessageIcon.Critical, 5000)
        logging.info(f"Tray error notification shown: {error}")
        # Fallback: use NotificationService if available
        if hasattr(self.app_instance, 'notification_service') and self.app_instance.notification_service:
            self.app_instance.notification_service.notify("JobOps Error", error)
            logging.info("Fallback notification service used.")
        # Also show error dialog
        QMessageBox.critical(None, "Generation Error", error)
    
    def on_message_clicked(self):
        logging.info("Tray message clicked.")
        pass
    
    def on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            logging.info("Tray icon double-clicked: opening generate letter dialog.")
            self.generate_letter()

class UploadWorker(QThread):
    """Background worker for document upload"""
    finished = Signal(str)
    error = Signal(str)
    
    def __init__(self, app_instance, file_path, doc_type):
        super().__init__()
        self.app_instance = app_instance
        self.file_path = file_path
        self.doc_type = doc_type
    
    def run(self):
        try:
            # Simulate document processing
            result = f"Document uploaded successfully: {os.path.basename(self.file_path)}"
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))

class GenerateWorker(QThread):
    """Background worker for letter generation"""
    finished = Signal(str)
    error = Signal(str)
    
    def __init__(self, app_instance, job_data):
        super().__init__()
        self.app_instance = app_instance
        self.job_data = job_data
    
    def run(self):
        try:
            logging.info("GenerateWorker started.")
            repository = getattr(self.app_instance, 'repository', None)
            generator = getattr(self.app_instance, 'generator', None)
            if repository is None or generator is None:
                logging.error("Application is missing repository or generator.")
                raise Exception("Application is missing repository or generator.")

            resume = repository.get_latest_resume()
            if resume is None:
                logging.error("No resume found. Please upload your resume first.")
                raise Exception("No resume found. Please upload your resume first.")

            from jobops.models import JobData
            import json as _json
            if not isinstance(self.job_data, JobData):
                job_data_obj = JobData(**self.job_data)
            else:
                job_data_obj = self.job_data

            logging.info(f"Generating letter for job: {job_data_obj}")
            letter = generator.generate(job_data_obj, resume)

            motivations_dir = os.path.expanduser("~/.jobops/motivations")
            import re
            import datetime
            safe_title = re.sub(r'[^a-zA-Z0-9_\-]', '_', job_data_obj.title or "letter")
            timestamp = (letter.generated_at if hasattr(letter, 'generated_at') else datetime.datetime.now()).strftime('%Y%m%d_%H%M%S')
            pdf_filename = f"{safe_title}_{timestamp}.pdf"
            pdf_path = os.path.join(motivations_dir, pdf_filename)
            export_letter_to_pdf(letter.content, pdf_path)

            reasoning_analysis = extract_reasoning_analysis(letter.content)
            job_data_clean = clean_job_data_dict(job_data_obj.dict())

            def default_encoder(obj):
                if hasattr(obj, 'isoformat'):
                    return obj.isoformat()
                raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")
            doc = Document(
                type=DocumentType.COVER_LETTER,
                filename=pdf_path,
                raw_content=letter.content,
                structured_content=letter.content,
                uploaded_at=letter.generated_at if hasattr(letter, 'generated_at') else None,
                reasoning_analysis=reasoning_analysis,
                job_data_json=_json.dumps(job_data_clean, default=default_encoder)
            )
            repository.save(doc)
            logging.info("Letter generation, PDF export, and storage completed.")
            self.finished.emit("Motivation letter generated, exported to PDF, and saved to database.")
        except Exception as e:
            logging.error(f"Exception in GenerateWorker: {e}")
            self.error.emit(str(e))

class JobOpsQtApplication(QApplication):
    """Main Qt application class"""
    
    def __init__(self, args):
        super().__init__(args)
        
        # Set application properties
        self.setApplicationName("JobOps")
        self.setApplicationVersion("2.0.0")
        self.setOrganizationName("JobOps")
        self.setQuitOnLastWindowClosed(False)  # Keep running in system tray
        
        # Initialize application data
        self.base_dir = Path.home() / ".jobops"
        self.base_dir.mkdir(exist_ok=True)

        # --- Load config and initialize repository and generator ---
        from jobops.repositories import SQLiteDocumentRepository
        from jobops.utils import ConcreteLetterGenerator
        from jobops.clients import LLMBackendFactory
        db_path = str(self.base_dir / "jobops.db")
        self.repository = SQLiteDocumentRepository(db_path)

        # Load config.json
        config_path = self.base_dir / "config.json"
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
        else:
            config = {}
        backend_type = config.get("backend", "ollama")
        backend_settings = config.get("backend_settings", {})
        app_settings = config.get("app_settings", {})
        tokens = app_settings.get("tokens", {})
        backend_conf = backend_settings.get(backend_type, {})
        # Use LLMBackendFactory to create the backend
        backend = LLMBackendFactory.create(backend_type, backend_conf, tokens)
        self.generator = ConcreteLetterGenerator(backend)
        # ---------------------------------------------------
        
        # Initialize components
        self.setup_logging()
        self.notification_service = NotificationService()
        self.system_tray = None
        
        self.setup_system_tray()
    
    def setup_logging(self):
        """Setup application logging"""
        log_file = self.base_dir / 'app.log'
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
    
    def setup_system_tray(self):
        """Initialize system tray"""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            QMessageBox.critical(
                None,
                "System Tray",
                "System tray is not available on this system."
            )
            sys.exit(1)
        
        self.system_tray = SystemTrayIcon(self)
        self.notification_service.set_system_tray(self.system_tray)
        self.system_tray.show()
        
        # Show startup notification
        self.system_tray.showMessage(
            "JobOps Started",
            "JobOps is running in the system tray. Right-click the icon to access features.",
            QSystemTrayIcon.MessageIcon.Information,
            3000
        )

def main():
    """Main application entry point"""
    
    # Check platform compatibility
    if not check_platform_compatibility():
        sys.exit(1)
    
    # Create Qt application
    app = JobOpsQtApplication(sys.argv)
    
    # Setup platform-specific features
    if sys.platform.startswith('linux'):
        create_desktop_entry()
    
    # Setup global shortcuts (if available)
    try:
        # Global shortcut for quick letter generation (Ctrl+Alt+J)
        shortcut = QShortcut(QKeySequence("Ctrl+Alt+J"), None)
        shortcut.activated.connect(app.system_tray.generate_letter)
        logging.info("Global shortcut registered: Ctrl+Alt+J")
    except Exception as e:
        logging.warning(f"Failed to setup global shortcut: {e}")
    
    # Show startup message
    logging.info("JobOps Qt application started successfully")
    
    # Start the application event loop
    try:
        sys.exit(app.exec())
    except KeyboardInterrupt:
        logging.info("Application interrupted by user")
        sys.exit(0)
    except Exception as e:
        logging.error(f"Application error: {e}")
        
        # Show error dialog
        QMessageBox.critical(
            None,
            "JobOps Error",
            f"An unexpected error occurred:\n\n{str(e)}\n\nPlease check the log file for details."
        )
        sys.exit(1)

if __name__ == "__main__":
    main()
