# JobOps Clipper Extension

A Chrome extension for clipping job postings and generating comprehensive application tracking reports using AI.

## Features

### Core Functionality

- **Web Page Clipping**: Extract job posting data from any webpage
- **Metadata Extraction**: Automatically capture title, description, requirements, and other job details
- **Markdown Generation**: Convert clipped content to structured markdown format

### AI-Powered Report Generation

- **Generate Report Button**: Creates comprehensive job application tracking reports
- **PDF Resume Integration**: Upload and extract content from PDF resumes
- **Dual LLM Support**:
  - **Primary**: Groq API with qwen2.5-32b-instant model (free tier with high usage limits)
  - **Fallback**: Local Ollama with qwen3:1.7b model

### Report Template

The extension generates detailed job application tracking reports including:

- Position details and requirements analysis
- Company research and competitive analysis
- Skills matrix and gap analysis
- Application materials tracking
- Interview scheduling and preparation
- Communication logs
- Performance assessment
- Outcome analysis and lessons learned

## Setup

### 1. Install Dependencies

```bash
npm install
```

### 2. Configure API Keys

- **Groq API Key**: Click the ⚙️ settings button in the extension popup to configure your Groq API key
- The extension will use Ollama as fallback if no Groq key is configured
- API keys are stored securely in Chrome's sync storage

### 3. Build Extension

```bash
npm run build
```

### 4. Load in Chrome

1. Open Chrome Extensions (chrome://extensions/)
2. Enable "Developer mode"
3. Click "Load unpacked"
4. Select the `dist/extension` folder

## Usage

### Basic Clipping

1. Navigate to a job posting page
2. Click the JobOps Clipper extension icon
3. Review extracted data in the popup
4. Use the 📋 button to copy markdown content

### Generate Comprehensive Report

1. Click the 📊 "Generate Report" button
2. Upload your PDF resume when prompted
3. The extension will:
   - Extract resume content from PDF
   - Send job data + resume to Groq API (or Ollama fallback)
   - Generate a comprehensive application tracking report
   - Display the filled report in the markdown editor



## Configuration

### Environment Variables

- `BACKEND_API_BASE`: Backend API URL (default: <http://localhost:8877>)
- `GROQ_API_KEY`: Groq API key (stored securely in Chrome sync storage)

### Permissions

- `scripting`: Execute content scripts
- `activeTab`: Access current tab
- `notifications`: Show status notifications
- `clipboardWrite`: Copy content to clipboard
- `storage`: Store API keys and settings

### Host Permissions

- `http://localhost:8877/*`: Backend API
- `https://api.groq.com/*`: Groq API
- `<all_urls>`: Content script injection

## Technical Details

### LLM Integration

- **Groq API**: Primary LLM with qwen2.5-32b-instant model
  - Free tier with generous usage limits (~20 jobs/day)
  - Fast response times
  - Structured output for report generation
- **Ollama Fallback**: Local LLM with qwen3:1.7b model
  - Runs locally for privacy
  - No API key required
  - Slower but more private

### PDF Processing

- Uses PDF.js library for text extraction
- Dynamically loads PDF.js from CDN if not available
- Extracts all text content from PDF resumes
- Handles multi-page documents

### Security

- API keys stored securely in Chrome sync storage
- No data sent to external services without user consent
- Local fallback option for privacy-conscious users
- PDF content processed locally before sending to LLM

## Development

### Project Structure

```
src/
├── background.ts      # Service worker
├── content.ts         # Content script
├── popup.ts          # Popup logic
├── popup.html        # Popup UI
├── popup.css         # Popup styling
└── icon.png          # Extension icon
```

### Build Process

1. TypeScript compilation
2. ESBuild bundling with environment variables
3. Asset copying (manifest, icons, HTML, CSS)
4. Output to `dist/extension/`

### Adding New Features

1. Update TypeScript files in `src/`
2. Modify HTML/CSS as needed
3. Update manifest.json for new permissions
4. Run `npm run build`
5. Reload extension in Chrome

## Troubleshooting

### Common Issues

- **PDF extraction fails**: Ensure PDF is not password-protected
- **Groq API errors**: Check API key in settings
- **Ollama not working**: Ensure Ollama is running locally with correct model
- **Build failures**: Check TypeScript compilation errors

### Logs

- Build logs: `build.log`
- Application logs: `application.log`
- Chrome DevTools: Check console for runtime errors

## License

MIT License - see LICENSE file for details.
