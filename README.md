# JobOps

[![PyPI version](https://img.shields.io/pypi/v/jobops.svg)](https://pypi.org/project/jobops/)
[![Build Status](https://github.com/codesapienbe/jobops-toolbar/workflows/CI/badge.svg)](https://github.com/codesapienbe/jobops-toolbar/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## AI-Powered Job Application Assistant

**JobOps** streamlines your job application process by scraping job postings, integrating with top AI backends, and generating personalized motivation letters in seconds.

---

## Table of Contents

- [Features](#features)
- [How It Works](#how-it-works)
- [Benefits](#benefits)
- [Screenshots](#screenshots)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage](#usage)
- [Configuration](#configuration)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

---

## Features

- **Multi-LLM Backend Support**: OpenAI, Ollama, Groq, and more.
- **Intelligent Job Scraping**: Automates data extraction from popular job boards.
- **Personalized Letters**: Generate tailored motivation letters in multiple languages.
- **Resume Profile Management**: Versioned profiles with customizable templates.
- **Electron-Based UI**: User-friendly desktop application with tabbed interface.
- **Batch Processing**: Generate letters at scale for agencies and teams.
- **History & Export**: View past letters and export as PDF or DOCX.

---

## How It Works

1. **Configure AI Backend**: Set up your preferred AI service (OpenAI, Groq, or local Ollama).
2. **Setup Profile**: Manage your resume and professional profile within the tray interface.
3. **Generate Letter**: Right-click the tray icon and select **Generate** to create a personalized motivation letter.
4. **Review & Save**: Edit generated letters as needed and save to your application history.

---

## Benefits

### What It Does

- Generate personalized motivation letters using AI.
- Scrape job descriptions from job posting URLs.
- Manage your resume profile seamlessly.
- Support multiple AI backends for flexibility.
- Minimal, tray-based interface for quick access.
- Work offline with local AI models.

### What It Doesn't Do

- Act as a recruiter or agency.
- Send applications automatically.
- Process applications for companies.
- Guarantee interview success.
- Replace human judgment and customization.

---

## Screenshots

<!-- Add your screenshot paths below -->

![Letter Generator](docs/screenshot-letter-generator.png)
![Configuration Tab](docs/screenshot-configuration.png)

---

## Installation

### End-User Installation

Install and launch the Tray Application in one step:

```bash
pip install jobops
jobops
```

Or zero-install via uvx:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
# Use the latest stable version
uvx --from https://github.com/codesapienbe/jobops/releases/download/v2025.06.27.1409/jobops-0.0.1-py3-none-any.whl 
```

### Developer Setup

```bash
pip install uv
uv pip install -e .
```

---

## Module Build Steps


### 0. Jobops CLI (Parent project)

```bash
uv sync
uv pip install -e .
# Build wheel (optional, for distribution)
uv build --out-dir ../../dist/jobops_cli/
# back to the parent dir
```


### 1. JobOps API (FastAPI Backend)

```bash
cd src/jobops_api
uv sync
uv pip install -e .
# Build wheel (optional, for distribution)
uv build --out-dir ../../dist/jobops_api/
# back to the parent dir
cd -
```

- Output: `dist/jobops_api/`

### 2. JobOps Tray (Tray Application)

```bash
cd src/jobops_tray
uv sync
uv pip install -e .
# Build wheel (optional, for distribution)
uv build --out-dir ../../dist/jobops_tray/
# back to the parent dir
cd -
```

- Output: `dist/jobops_tray/`

### 3. JobOps Clipper (Chrome Extension)

```bash
cd src/jobops_clipper
npm install
npm run build
# back to the parent dir
cd -
```

- Output: `dist/jobops_clipper/` (at project root)

---


## Configuration

Configure AI backends, templates, and repository paths in:

- `~/.jobops/config.yml`
- Environment variables: `JOBOPS_OPENAI_API_KEY`, `JOBOPS_OLLAMA_PORT`, etc.

---

## Required API Port Configuration

The JobOps API **requires** the environment variable `JOBOPS_API_PORT` to be set before starting the API server or using the CLI to launch the API. There is **no default port**; you must specify the port explicitly via the environment variable.

### Example Usage

```bash
export JOBOPS_API_PORT=8081
jobops  # or python -m jobops_api
```

If `JOBOPS_API_PORT` is not set or is not a valid integer, the API and CLI will raise an error and refuse to start.

- **Error if not set:**
  - `RuntimeError: Environment variable JOBOPS_API_PORT must be set (no default port allowed).`
- **Error if not integer:**
  - `RuntimeError: JOBOPS_API_PORT must be an integer, got: <value>`

Set this variable in your shell or environment before running JobOps services.

---

## Roadmap

- 📱 Mobile applications (iOS & Android)
- 🌐 More job board integrations
- 🧠 Advanced AI features and plugins
- 📄 Custom workplace templates

---

## Contributing

We welcome contributions! Please read our [CONTRIBUTING](CONTRIBUTING.md) guidelines.

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

## Contact

Created by the JobOps Team. For questions or feedback, open an issue or reach out via email: `support@jobops.com`.
