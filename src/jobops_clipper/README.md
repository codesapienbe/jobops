# JobOps Clipper Extension

A Chrome extension for clipping job postings and generating comprehensive application tracking reports using AI.

## Features

### Core Functionality

- **Web Page Clipping**: Extract job posting data from any webpage
- **Metadata Extraction**: Automatically capture title, description, requirements, and other job details
- **Markdown Generation**: Convert clipped content to structured markdown format
- **Multi-Language Support**: Full internationalization with 4 supported languages (EN, NL, FR, TR)

### AI-Powered Report Generation

- **Generate Report Button**: Creates comprehensive job application tracking reports
- **PDF Resume Integration**: Upload and extract content from PDF resumes
- **Dual LLM Support**:
  - **Primary**: Groq API with qwen2.5-32b-instant model (free tier with high usage limits)
  - **Fallback**: Local Ollama with qwen3:1.7b model

### Linear Integration

- **Export to Linear**: Send job applications directly to Linear as tasks and subtasks
- **Smart Task Mapping**: Creates main task + 16 subtasks for each job application section
- **Comprehensive Content**: Includes all job data, requirements, and tracking information
- **Automatic Organization**: Uses Linear labels and priorities for better organization
- **Direct Access**: Automatically opens created tasks in Linear for immediate access

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
- **Linear API Key**: Configure Linear integration for task creation (API key + team ID required)
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

### Export to Linear

1. Configure Linear API key and team ID in settings (⚙️ button)
2. Click the 📤 "Export to Linear" button
3. The extension will:
   - Create a main task for the job application
   - Generate 16 subtasks for each application section
   - Include all job data and tracking information
   - Automatically open the created task in Linear

## Database Overview

The JobOps Clipper extension uses IndexedDB (a local browser database) to store job application data with proper table relationships. The system prevents duplicate applications by using canonical URLs as unique identifiers.

### Database Architecture

#### Main Tables

1. **job_applications** - Main table containing basic job application information
   - `id` (Primary Key)
   - `canonical_url` (Unique Index) - Prevents duplicate applications
   - `job_title`
   - `company_name`
   - `application_date`
   - `status`
   - `created_at`
   - `updated_at`

#### Section Tables

All section tables have a foreign key relationship to `job_applications` via `job_application_id`:

2. **position_details** - Job position information
3. **job_requirements** - Required skills and qualifications
4. **company_information** - Company details and research
5. **skills_matrix** - Skills assessment framework
6. **skill_assessments** - Individual skill assessments (linked to skills_matrix)
7. **application_materials** - Resume, cover letter, and documents
8. **interview_schedule** - Interview appointments and details
9. **interview_preparation** - Preparation checklist and notes
10. **communication_log** - All communications with the company
11. **key_contacts** - Important contact information
12. **interview_feedback** - Interview performance and feedback
13. **offer_details** - Job offer information
14. **rejection_analysis** - Rejection reasons and lessons
15. **privacy_policy** - Privacy and consent tracking
16. **lessons_learned** - Insights and improvements
17. **performance_metrics** - Application success metrics
18. **advisor_review** - Professional advisor feedback

### Database - Key Features

#### URL-Based Uniqueness

- Uses canonical URLs (without query parameters or fragments) to prevent duplicate applications
- Automatically detects existing applications when visiting the same job posting
- Loads existing data if found, creates new record if not

#### Data Relationships

- All section data is linked to the main job application via `job_application_id`
- Hierarchical relationships (e.g., skill_assessments linked to skills_matrix)
- Maintains referential integrity

#### Data Persistence

- All data is stored locally in the browser using IndexedDB
- No external dependencies or network requirements
- Automatic backup and restore capabilities

### Repository Usage

#### Creating a New Job Application

```typescript
// Check if job already exists
const jobExists = await jobOpsDataManager.checkAndLoadExistingJob(url);
if (!jobExists) {
  // Create new job application
  const jobId = await jobOpsDataManager.createNewJobApplication(jobData);
}
```

#### Saving Section Data

```typescript
// Save position details
await jobOpsDataManager.savePositionDetails({
  jobTitle: "Software Engineer",
  companyName: "Tech Corp",
  location: "San Francisco, CA",
  // ... other fields
});

// Save job requirements
await jobOpsDataManager.saveJobRequirements({
  requiredSkills: ["JavaScript", "React", "Node.js"],
  preferredSkills: ["TypeScript", "AWS"],
  // ... other fields
});
```

#### Loading Complete Application

```typescript
// Load all data for a job application
const completeData = await jobOpsDataManager.getCompleteJobApplication(jobId);
```

#### Updating Job Status

```typescript
// Update application status
await jobOpsDataManager.updateJobStatus('interview_scheduled');
```

### Database Operations

#### Core Operations

- **Create**: `createJobApplication()`
- **Read**: `getJobApplication()`, `getCompleteJobApplication()`
- **Update**: `updateJobApplication()`, `updateSectionData()`
- **Delete**: `deleteJobApplication()`

#### Section Operations

- **Save**: `saveSectionData()` for each section type
- **Load**: `getSectionDataByJobId()` for each section type
- **Update**: `updateSectionData()` for existing records

#### Utility Operations

- **Check Existence**: `checkJobApplicationExists()`
- **Export**: `exportDatabase()` for backup
- **Import**: `importDatabase()` for restore
- **Clear**: `clearDatabase()` for reset

### Data Flow

1. **Page Load**: Extension checks if job application exists for current URL
2. **Existing Job**: Loads all section data and populates UI
3. **New Job**: Creates new job application record
4. **Data Entry**: User fills out sections, data is saved automatically
5. **Status Updates**: Job status is updated as application progresses
6. **Export/Import**: Data can be backed up and restored

### Security & Privacy

- All data is stored locally in the browser
- No data is transmitted to external servers (except for AI analysis)
- User has full control over their data
- Privacy policy tracking for compliance

### Performance

- IndexedDB provides fast local storage
- Efficient queries using indexes on `canonical_url` and `job_application_id`
- Minimal memory footprint
- Automatic cleanup of old data

### Error Handling

- Comprehensive error logging to application.log
- Graceful fallbacks for database operations
- User-friendly error messages
- Data validation before saving

### Future Enhancements

- Cloud sync capabilities
- Advanced search and filtering
- Data analytics and insights
- Integration with external job platforms
- Multi-user support
- Advanced backup strategies

## Configuration

### Environment Variables

- `BACKEND_API_BASE`: Backend API URL (default: <http://localhost:8877>)
- `GROQ_API_KEY`: Groq API key (stored securely in Chrome sync storage)
- `LINEAR_API_KEY`: Linear API key (stored securely in Chrome sync storage)
- `LINEAR_TEAM_ID`: Linear team ID for task creation

### Permissions

- `scripting`: Execute content scripts
- `activeTab`: Access current tab for on-demand script injection
- `notifications`: Show status notifications
- `clipboardWrite`: Copy content to clipboard
- `storage`: Store API keys and settings

### Host Permissions

- `http://localhost:8877/*`: Backend API
- `https://api.groq.com/*`: Groq API
- `https://api.linear.app/*`: Linear API
- `https://libretranslate.de/*`: Translation API (primary)
- `https://translate.argosopentech.com/*`: Translation API (fallback)

The extension injects `content.js` on-demand using `activeTab` + `scripting.executeScript`, eliminating the need for `<all_urls>` optional host permissions.

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

### Linear Integration

- **GraphQL API**: Full Linear API integration using GraphQL
- **Task Creation**: Creates main task with job application overview
- **Subtask Generation**: Automatically creates 16 subtasks for each section
- **Smart Mapping**: Maps job data to appropriate Linear task descriptions
- **Label Integration**: Uses Linear labels for better organization
- **Priority Management**: Sets appropriate priorities for tasks and subtasks

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
- Linear API keys encrypted and stored securely

### Internationalization (i18n)

The extension supports multiple languages with automatic language detection and dynamic content translation:

- **Supported Languages**: English (US), Dutch (Belgium), French (Belgium), Turkish (Turkey)
- **Language Detection**: Automatically detects browser language on first use
- **Language Switching**: Click the 🌐 button to change language in real-time
- **Dynamic Translation**: Existing content is automatically translated when switching languages
- **Free Translation APIs**: Uses LibreTranslate and Argos Translate for dynamic content translation
- **Persistent Preferences**: Language choice is saved and persists across sessions

See `src/locales/README.md` for detailed documentation on the i18n system.

## Security

- Content Security Policy: The popup includes a strict CSP disallowing inline scripts/styles, permitting only required connect-src endpoints.
- HTML sanitization: All HTML rendered in the popup (e.g., real-time response fragments) is sanitized via DOMPurify; dynamic text uses textContent.
- Secrets handling: API keys are stored in Chrome sync storage and never logged. UI masks secrets with show/hide toggles. Crash/console logs redact likely PII.
- Optional encryption: IndexedDB payloads can be encrypted with a user-provided passphrase (AES-GCM with PBKDF2-derived key). Passphrase is not stored.
- Consent: Users must opt-in before sending data to Groq/Linear.

See `src/popup.html` for CSP meta tag and `src/popup.ts` for sanitization and consent enforcement.

## Development

### Project Structure

```
src/
├── background.ts      # Service worker
├── content.ts         # Content script
├── popup.ts          # Popup logic
├── popup.html        # Popup UI
├── popup.css         # Popup styling
├── i18n.ts           # Internationalization manager
├── client.ts         # API clients (Linear, etc.)
├── integration.ts    # Integration services (Linear, etc.)
├── locales/          # Language files
│   ├── en.json       # English translations
│   ├── nl.json       # Dutch translations
│   ├── fr.json       # French translations
│   └── tr.json       # Turkish translations
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

## Build Scripts

- `npm run build:dev`: Fast dev build with watch and sourcemaps
- `npm run build:prod`: Optimized production build (minified + sourcemaps)
- `npm run clean`: Cross-platform clean using rimraf

## Permissions Rationale

This extension follows the principle of least privilege:

- **activeTab**: Grants temporary access to the current tab when the user interacts, enabling on-demand script injection
- **optional_host_permissions: <all_urls>**: Required only to inject `content.js` on-demand into user-initiated pages; permission is optional and requested at runtime
- **host_permissions**: Specific APIs used by features
  - Backend API (`http://localhost:8877/*`)
  - Groq API (`https://api.groq.com/*`)
  - Linear API (`https://api.linear.app/*`)
  - Translation APIs (LibreTranslate/Argos)

The extension no longer auto-injects `content.js` on all sites. Instead, it injects on-demand via `activeTab`, reducing always-on permissions and improving privacy.
