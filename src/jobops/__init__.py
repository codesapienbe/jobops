import sys
import os
import logging
import base64
import tempfile
from pathlib import Path
import webbrowser
from PIL import Image
from io import BytesIO

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

# Other imports (install these via pip if not available)
from dotenv import load_dotenv

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

class ResourceManager:
    """Manages embedded and temporary resources"""
    
    @staticmethod
    def create_app_icon():
        """Create application icon from embedded data or generate programmatically"""
        try:
            # Try to decode embedded icon
            icon_data = base64.b64decode(EMBEDDED_ICON_DATA)
            pixmap = QPixmap()
            pixmap.loadFromData(icon_data)
            if not pixmap.isNull():
                return QIcon(pixmap)
        except Exception:
            pass
        
        # Fallback: create icon programmatically
        pixmap = QPixmap(64, 64)
        pixmap.fill(QColor(70, 130, 180))
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw background circle
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        painter.setPen(QPen(QColor(70, 130, 180), 2))
        painter.drawEllipse(8, 8, 48, 48)
        
        # Draw "J" letter
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
        """Get or create temporary directory for the application"""
        temp_dir = Path(tempfile.gettempdir()) / "jobops_qt"
        temp_dir.mkdir(exist_ok=True)
        return temp_dir

class NotificationService(QObject):
    """Cross-platform notification service using Qt"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.system_tray = None
    
    def set_system_tray(self, tray_icon):
        self.system_tray = tray_icon
    
    def notify(self, title: str, message: str) -> None:
        """Show notification using system tray or fallback"""
        try:
            if self.system_tray and QSystemTrayIcon.isSystemTrayAvailable():
                self.system_tray.showMessage(
                    title, 
                    message, 
                    QSystemTrayIcon.MessageIcon.Information, 
                    3000
                )
            else:
                # Fallback to message box if system tray not available
                QMessageBox.information(None, title, message)
        except Exception as e:
            logging.warning(f"Notification failed: {e}")

class JobInputDialog(QDialog):
    """Modern job input dialog"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Generate Motivation Letter")
        self.setFixedSize(650, 500)
        self.setWindowIcon(ResourceManager.create_app_icon())
        
        self.job_data = None
        self.setup_ui()
    
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
        
        details_layout.addRow("Company Name:", self.company_input)
        details_layout.addRow("Job Title:", self.title_input)
        details_layout.addRow("Location:", self.location_input)
        details_layout.addRow("Contact Person:", self.contact_input)
        
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
            'location': self.location_input.text().strip(),
            'contact_info': self.contact_input.text().strip()
        }
        
        self.accept()

    def closeEvent(self, event):
        if hasattr(self, 'generate_worker') and self.generate_worker.isRunning():
            self.generate_worker.wait()
        event.accept()

class UploadDialog(QDialog):
    """File upload dialog"""
    
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
        self.accept()

class SystemTrayIcon(QSystemTrayIcon):
    """Custom system tray icon with JobOps functionality"""
    
    def __init__(self, app_instance, parent=None):
        super().__init__(parent)
        self.app_instance = app_instance
        self.setup_tray()
    
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
        """Show upload dialog"""
        dialog = UploadDialog()
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Process upload in background thread
            worker = UploadWorker(self.app_instance, dialog.file_path, dialog.doc_type)
            worker.finished.connect(self.on_upload_finished)
            worker.error.connect(self.on_upload_error)
            worker.start()
    
    def generate_letter(self):
        """Show job input dialog and generate letter"""
        
        dialog = JobInputDialog()
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.generate_worker = GenerateWorker(self.app_instance, dialog.job_data)
            self.generate_worker.finished.connect(self.on_generation_finished)
            self.generate_worker.error.connect(self.on_generation_error)
            self.generate_worker.start()
    
    def download_letters(self):
        """Show download dialog"""
        # Implementation for downloading letters
        QMessageBox.information(None, "Download", "Download functionality will be implemented here.")
    
    def show_settings(self):
        """Show settings dialog"""
        # Implementation for settings
        QMessageBox.information(None, "Settings", "Settings dialog will be implemented here.")
    
    def show_help(self):
        """Open help/documentation"""
        webbrowser.open("https://github.com/codesapienbe/jobops-toolbar")
    
    def quit_application(self):
        """Quit the application"""
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
        """Handle upload completion"""
        self.showMessage("JobOps", message, QSystemTrayIcon.MessageIcon.Information, 3000)
    
    def on_upload_error(self, error):
        """Handle upload error"""
        self.showMessage("JobOps Error", error, QSystemTrayIcon.MessageIcon.Critical, 5000)
    
    def on_generation_finished(self, message):
        """Handle generation completion"""
        self.showMessage("JobOps", message, QSystemTrayIcon.MessageIcon.Information, 3000)
    
    def on_generation_error(self, error):
        """Handle generation error"""
        self.showMessage("JobOps Error", error, QSystemTrayIcon.MessageIcon.Critical, 5000)
    
    def on_message_clicked(self):
        """Handle tray message click"""
        pass
    
    def on_tray_activated(self, reason):
        """Handle tray icon activation"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
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
            # Ensure repository and generator are available
            repository = getattr(self.app_instance, 'repository', None)
            generator = getattr(self.app_instance, 'generator', None)
            if repository is None or generator is None:
                raise Exception("Application is missing repository or generator.")

            # Get the latest resume
            resume = repository.get_latest_resume()
            if resume is None:
                raise Exception("No resume found. Please upload your resume first.")

            # Convert job_data dict to JobData model if needed
            from jobops.models import JobData
            if not isinstance(self.job_data, JobData):
                job_data_obj = JobData(**self.job_data)
            else:
                job_data_obj = self.job_data

            # Generate the motivation letter
            letter = generator.generate(job_data_obj, resume)
            result = letter.content
            self.finished.emit(result)
        except Exception as e:
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

        # --- Add repository and generator initialization ---
        from jobops.repositories import SQLiteDocumentRepository
        from jobops.utils import ConcreteLetterGenerator
        from jobops.clients import OllamaBackend
        db_path = str(self.base_dir / "jobops.db")
        self.repository = SQLiteDocumentRepository(db_path)
        self.generator = ConcreteLetterGenerator(OllamaBackend())
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

def check_platform_compatibility():
    """Check if the current platform is supported"""
    platform_info = {
        'system': os.name,
        'platform': sys.platform,
        'qt_available': QT_AVAILABLE
    }
    
    logging.info(f"Platform info: {platform_info}")
    
    if not QT_AVAILABLE:
        print("Qt is not available. Please install PySide6 or PyQt6.")
        return False
    
    return True

def create_desktop_entry():
    """Create desktop entry for Linux systems"""
    if sys.platform.startswith('linux'):
        try:
            desktop_dir = Path.home() / '.local' / 'share' / 'applications'
            desktop_dir.mkdir(parents=True, exist_ok=True)
            
            desktop_file = desktop_dir / 'jobops.desktop'
            script_path = Path(__file__).absolute()
            
            desktop_content = f"""[Desktop Entry]
Name=JobOps
Comment=AI Motivation Letter Generator
Exec=python3 "{script_path}"
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
