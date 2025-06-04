# JobOps Toolbar - AI-Powered Job Application Assistant

**For Job Seekers and Developers**

---

## Overview

JobOps Toolbar is a Python application designed to help job seekers quickly generate personalized motivation letters and manage job application workflows using multiple AI backends. It also provides a robust, extensible codebase for developers to contribute and extend its functionality.

---

## What does it do?

- **For End-Users:**
  - Paste a job posting URL, company name, job title, and location.
  - The app scrapes the job page for the job description.
  - It uses your resume and the job details to generate a tailored motivation letter.
  - Output: a ready-to-send motivation letter.
- **For Developers:**
  - Modular, extensible architecture under `src/jobops/`.
  - Easily add new scrapers, AI backends, or UI features.

---

## What it does NOT do

- Does **not** act as a recruiter or agency.
- Does **not** send applications automatically or on your behalf.
- Does **not** process applications for companies.

---

## Quick Start (End-Users)

### Prerequisites

- Python 3.8 or higher
- Internet connection for AI backends and job scraping
- 4GB RAM recommended for local AI models

### Installation

1. **Clone the Repository**

   ```bash
   git clone https://github.com/codesapienbe/jobops-toolbar.git
   cd jobops-toolbar
   ```

2. **Install Dependencies**

   ```bash
   pip install .
   # or, if you prefer pip-tools:
   pip install -r uv.lock
   ```

   Or, for editable/development mode:

   ```bash
   pip install -e .
   ```

3. **Run the Application**

   ```bash
   # If a GUI/CLI entrypoint is provided (update as needed):
   python -m jobops
   # Or, if built as an executable:
   ./jobops.exe
   ```

---

## Features

- **Multi-LLM Backend Support:** OpenAI, Ollama (local), Groq
- **Intelligent Job Scraping:** Extracts job descriptions from most job sites
- **Personalized Letter Generation:** AI-powered, multi-language, context-aware
- **Resume Management:** Integrated CV editor, skills, experience, education
- **Modern UI:** Tabbed interface, real-time status, history, export
- **Advanced Automation:** Batch processing, template management, cross-platform

---

## Configuration

### AI Backend Setup

- **OpenAI:** Enter your API key in the configuration UI.
- **Groq:** Enter your API key in the configuration UI.
- **Ollama (Local):**
  - Install [Ollama](https://ollama.ai/)
  - Start Ollama: `ollama serve`
  - Download a model: `ollama pull llama3.1`
  - Configure the URL in settings (default: <http://localhost:11434>)

### Resume Profile Setup

- Use the Resume tab in the UI to enter and save your professional information.

---

## Usage Guide

1. **Configure your AI backend** in the Configuration tab.
2. **Set up your professional profile** in the Resume tab.
3. **Generate a motivation letter** in the Letter Generator tab by pasting a job URL and filling in details.
4. **Review, edit, and save** your generated letter.
5. **Access saved letters** in the History tab.

---

## Project Structure

```text
jobops-toolbar/
├── src/
│   └── jobops/
│       ├── clients/
│       ├── config/
│       ├── models/
│       ├── repositories/
│       ├── scrapers/
│       ├── services/
│       ├── utils/
│       └── views/
├── pyproject.toml
├── uv.lock
├── README.md
├── jobops.exe.spec
└── .jobops/           # User data directory (created at runtime)
```

- **src/jobops/**: All core application code (modular, extensible)
- **pyproject.toml**: Project metadata and dependencies
- **uv.lock**: Locked dependencies (if using pip-tools/uv)
- **.jobops/**: User config, resume data, saved letters, logs (created at runtime)

---

## Developer Guide

### Setup

1. **Clone and enter the repo:**

   ```bash
   git clone https://github.com/codesapienbe/jobops-toolbar.git
   cd jobops-toolbar
   ```

2. **Create a virtual environment:**

   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

3. **Install in editable mode:**

   ```bash
   pip install -e .
   ```

4. **Run tests (if available):**

   ```bash
   python -m pytest
   ```

### Contributing

- Follow PEP 8 style guidelines
- Add docstrings and unit tests for new features
- Update documentation as needed
- Ensure cross-platform compatibility

### Directory Overview

- **clients/**: API and backend clients (OpenAI, Groq, Ollama, etc.)
- **config/**: Configuration management
- **models/**: Data models
- **repositories/**: Data persistence and access
- **scrapers/**: Job description scrapers
- **services/**: Business logic and orchestration
- **utils/**: Utility functions
- **views/**: UI components (Tkinter, etc.)

---

## Troubleshooting

- **Backend Error: API key required**: Check your API key in the configuration.
- **Scraping Failed**: Try a different job URL or enter the job description manually.
- **Model not found (Ollama)**: Ensure the model is downloaded and Ollama is running.
- **Application Won't Start**: Check Python version and dependencies.
- **Poor Letter Quality**: Complete your resume and try a different AI model.

---

## License

JobOps Toolbar is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## Support & Community

- **GitHub Issues**: Report bugs and request features
- **Discussions**: Ask questions and share experiences
- **Wiki**: Community-maintained documentation and tips
- **Email**: <support@jobops.dev>
- **Docs**: <https://docs.jobops.dev>

---

> **Built with ❤️ for job seekers and developers worldwide**
