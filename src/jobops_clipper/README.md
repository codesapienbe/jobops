# JobOps Clipper

A secure, local-first Chrome extension and backend service for clipping web content and sending it to your JobOps desktop app.

---

## Overview

**JobOps Clipper** enables you to extract ("clip") content from any web page and send it as structured JSON (e.g., Markdown) to your locally running JobOps app. Inspired by Obsidian Web Clipper, this tool is designed for privacy, security, and seamless integration with your workflow.

- **Chrome Extension:** Written in TypeScript, extracts and serializes web content, then sends it to your local JobOps backend.
- **Backend Service:** Python Flask app, receives clips and stores them securely for JobOps to process.
- **Local-Only:** No data leaves your machine. No Chrome Store publishing required.

---

## Architecture

```
[Chrome Extension (TypeScript)]
        │
        ▼
[Local Flask Backend (Python)]
        │
        ▼
[JobOps App / File System]
```

- **Content Script:** Extracts and serializes web page content.
- **Background Script:** Handles user actions and communication with backend.
- **Flask Backend:** Receives, validates, and stores clipped data.

---

## Security & Privacy

- **Local Communication Only:** All data is sent to `http://localhost:<PORT>`.
- **No Cloud, No Tracking:** Your data never leaves your device.
- **Input Validation & Sanitization:** All incoming data is validated and sanitized before storage.
- **Minimal Permissions:** Extension requests only the permissions it needs.
- **No Sensitive Data in Logs:** All logs are sanitized and written to `application.log` in structured JSON format.

---

## Prerequisites

- **Node.js** (v16+ recommended)
- **npm** (v8+ recommended)
- **Python** (3.8+)
- **pip**
- **UV**
- **Google Chrome** (latest)

---

## Setup Instructions

### 1. Clone the Repository

```sh
git clone <your-repo-url>
cd jobops/src/jobops-clipper
```

### 2. Backend (Flask) Setup

```sh
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

- The backend will listen on `http://localhost:5000/clip` by default.
- All received clips are stored in the `clips/` directory.

#### Configuration

- To change the port or storage directory, edit `backend/app.py`.

### 3. Chrome Extension Setup

```sh
cd extension
npm install
npm run build
```

> Note: TypeScript type support for Chrome APIs is provided by `@types/chrome`, which is installed automatically as a dev dependency.

#### Load Unpacked Extension

1. Open Chrome and go to `chrome://extensions/`
2. Enable **Developer mode** (top right)
3. Click **Load unpacked**
4. Select the `extension/dist` directory

#### Configuration

- The extension is pre-configured to send data to `http://localhost:5000/clip`.
- To change the endpoint, edit `src/config.ts` in the extension source.

---

## Usage

1. Start the Flask backend (`python app.py`)
2. Load the extension in Chrome
3. Navigate to any web page
4. Click the JobOps Clipper icon to clip the page
5. The content will be sent to your JobOps app (or stored in `clips/`)

---

## Best Practices

- **Keep your backend running** while using the extension.
- **Review and sanitize** all received data before further processing.
- **Monitor `application.log`** for errors or warnings.
- **Update dependencies** regularly for security.

---

## Security Notes

- The backend only accepts requests from `localhost`.
- All input is validated and sanitized before file operations.
- No authentication is required for local use, but you may add a token for extra protection.
- Never expose the backend to the public internet without additional security measures.

---

## Directory Structure

```
jobops-clipper/
  backend/           # Flask backend service
    app.py
    requirements.txt
    application.log
    clips/
  extension/         # Chrome extension (TypeScript)
    src/
    dist/
    manifest.json
    package.json
    tsconfig.json
  README.md
```

---

## Troubleshooting

- **Extension not working?** Ensure the backend is running and accessible at the configured port.
- **CORS errors?** The backend is configured to allow local extension requests.
- **Permission issues?** Make sure Chrome has access to the extension and the backend can write to `clips/`.

---

## Contributing

- Follow secure coding practices (see [OWASP Top 10](https://owasp.org/www-project-top-ten/)).
- Use structured logging and sanitize all logs.
- Keep business logic and workflows intact.
- Submit focused pull requests (one logical change at a time).

---

## License

MIT License. See [LICENSE](../LICENSE) for details.

---

## Local Installation & Running

### 1. Build and Install Dependencies

From the project root, run:

```sh
./pyven.sh install
```

- This will sync Python dependencies, build the Python package, and install/build the Chrome extension.

### 2. Start the Backend

From the project root, run:

```sh
uv run jobops-clipper
```

- This starts the Flask backend on `http://localhost:5000`.

### 3. Start the JobOps Desktop App

From the project root, run:

```sh
uv run jobops
```

- This starts the main JobOps desktop application. Ensure both the backend and the desktop app are running for full integration.

### 4. Load the Chrome Extension in Google Chrome

1. Open Google Chrome.
2. Go to `chrome://extensions/` in the address bar.
3. Enable **Developer mode** (toggle in the top right).
4. Click **Load unpacked**.
5. Select the `src/jobops-clipper/extension/dist` directory.
6. The JobOps Clipper extension should now appear in your extensions list.

### 5. Using the Clipper

1. Ensure both the JobOps desktop app and the backend are running.
2. Navigate to any web page you want to clip.
3. Click the **JobOps Clipper** extension icon in the Chrome toolbar.
4. You should see a notification indicating success or error.
5. Clipped content will be saved as a Markdown file in the `clips/` directory (where the backend is running), and can be processed by the JobOps app.

### 6. Troubleshooting

- If you see errors:
  - Ensure both the backend and the JobOps desktop app are running and accessible.
  - Check Chrome’s extension errors (click the “Errors” link in the extension card).
  - Review `application.log` for backend issues.

---
