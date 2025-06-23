# JobOps Toolbar - AI-Powered Job Application Assistant

**An AI-powered application to streamline job applications and generate personalized motivation letters.**

## Introduction

JobOps Toolbar helps job seekers automate and personalize their job application process. By scraping job postings, integrating various AI backends, and providing an intuitive desktop UI, it accelerates motivation letter generation and workflow management.

## Use Cases

- **Individual Applicants**: Generate tailored motivation letters quickly for each job posting.
- **Recruitment Agencies**: Batch-generate personalized letters for multiple candidates.
- **HR Teams**: Maintain and re-use templates across the organization.
- **Developers**: Extend backend integrations, scrapers, and UI features.

## Features

- Multi-LLM Backend Support (OpenAI, Ollama, Groq).
- Intelligent Job Scraping from popular job boards.
- Personalized, multi-language motivation letter generation.
- Resume Profile Management with version control.
- Electron-based Desktop UI with tabbed interface.
- Batch Processing and Template Management.
- History and Export Options (PDF, DOCX).

## Architecture

![Architecture Diagram](docs/architecture.png)

1. **Scrapers**: Fetch and parse job descriptions.
2. **Pipeline**: Normalize data and orchestrate AI calls.
3. **Clients & Services**: Wrap AI backend APIs and business logic.
4. **Views**: Electron front-end components (Configuration, Resume, Letter Generator).
5. **Repositories & Models**: Store user profiles and history.
6. **Utils**: Shared helpers (logging, validation).

## Modules & Project Structure

```
src/jobops/
├── clients/       # AI backend integration
├── config/        # Configuration schemas and loaders
├── models/        # Domain and data models
├── pipeline/      # Core processing flow
├── repositories/  # Persistence (files, DB)
├── scrapers/      # Job posting scrapers
├── services/      # Business logic services
├── utils/         # Utility functions
└── views/         # Electron front-end code
```

## Technology Stack

- **Backend**: Python 3.8+ (FastAPI for local API, internal modules).
- **Frontend**: Electron (Node.js, app.js, index.html, style.css).
- **AI Backends**: OpenAI API, Ollama, Groq.
- **Packaging**: setuptools, pyinstaller.
- **Testing**: pytest.

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Node.js & npm (for Electron)
- Internet connection for scraping and AI services

### Clone & Build

```bash
git clone https://github.com/codesapienbe/jobops-toolbar.git
cd jobops-toolbar
```

- **Backend**:

```bash
pip install -e .
```

- **Frontend** (in a separate terminal):

```bash
cd docs
npm install
npm run build
```

### Desktop Client

Launch the Electron-based desktop application:

```bash
npm start # from docs directory
# or, run the packaged executable:
./dist/jobops-toolbar.exe
```

### Mobile App (Future Plan)

A cross-platform mobile application (iOS/Android) is planned. Stay tuned for updates.

## Manual Testing Guide

1. Start the desktop client.
2. Configure an AI backend in the **Configuration** tab.
3. Add or edit your resume profile in the **Resume** tab.
4. Paste a job URL, fill in details, and generate a letter in the **Letter Generator** tab.
5. Review and export the generated letter.
6. Validate scraping accuracy, letter quality, and error handling.

## Developer Guide

- **Adding Scrapers**: Create a new class in `src/jobops/scrapers/` implementing the `BaseScraper` interface.
- **New AI Backend**: Add a client under `src/jobops/clients/` and register it in `config`.
- **UI Development**: Modify or extend Electron views in `docs/` (React/Vanilla JS).
- **Testing**: Write tests under `test/` and run `pytest`.
- **Code Style**: Follow PEP8. Use `black` and `flake8` for formatting and linting.

## Packaging & Deployment

- **Python Package**:

```bash
python setup.py sdist bdist_wheel
```

- **Executable**:

```bash
pyinstaller --onefile --name jobops-toolbar jobops/__main__.py
```

- **Releases**: Use GitHub Actions for CI/CD, auto-publish to PyPI and GitHub Releases.

## Run with uvx (zero-install)

If you have the [uv](https://github.com/astral-sh/uv) package manager installed, you can run JobOps without cloning or installing it system-wide:

```bash
# Install uv once (if you don't have it yet)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Run the latest released version of JobOps in an isolated environment
uvx jobops  # or specify a version: uvx [email protected]
```

`uvx` will download the wheel that was published in the CI step above, create a temporary virtual environment, install JobOps and all its dependencies, and finally invoke the `jobops` CLI. Nothing is left behind except for a cached copy of the packages, so subsequent runs start instantly.

> Tip: If you are testing a pre-release or a commit that hasn't been published to PyPI yet, you can point `uvx` at the wheel attached to a GitHub release artifact:
>
> ```bash
> uvx --from "https://github.com/<org>/jobops-toolbar/releases/download/<tag>/jobops-<version>-py3-none-any.whl" jobops
> ```

## FAQ

**Q: I get "API key required" errors.**
A: Ensure your API key is set in Configuration > AI Backends.

**Q: Scraping fails on certain sites.**
A: Use manual input or extend the scraper for that site.

**Q: "Model not found" with Ollama.**
A: Run `ollama serve` and `ollama pull llama3.1` before launching.

**Q: Letter quality is poor.**
A: Complete your resume profile and try different AI models.

## Contributing

We welcome contributions:

1. Fork the repository.
2. Create a feature branch: `git checkout -b feature/my-feature`.
3. Commit changes with clear messages.
4. Push to your fork and open a Pull Request.
5. Ensure tests pass and code is linted.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
