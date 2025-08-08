# Jobops Clipper (Chrome Extension) TODO List

- [x] Add a new feature that will allow users to send the clipboard data directly to Linear
- [x] It will create a new Linear task, and for each section, it will create an apart sub-task and add their contents in it.
- [x] It should use Linear API or if exists Linear SDK for typescript.

## ✅ Linear Integration Completed

### Features Implemented

- **Linear API Client**: Full GraphQL API integration with TypeScript
- **Task Creation**: Creates main task for job application with comprehensive details
- **Subtask Generation**: Automatically creates 16 subtasks for each job application section
- **Smart Content Mapping**: Maps job data to appropriate Linear task descriptions
- **Settings Integration**: Enhanced settings dialog with Linear configuration
- **Error Handling**: Comprehensive error handling and user feedback
- **Security**: Secure API key storage in Chrome sync storage

### Technical Implementation

- `client.ts`: GraphQL client for Linear API (and future clients)
- `integration.ts`: Service layer for job-to-task mapping (and future integrations)
- Enhanced `popup.ts`: UI integration with export button
- Updated `manifest.json`: Added Linear API permissions
- Enhanced settings: Modal dialog for Linear configuration

### Usage

1. Configure Linear API key and team ID in settings
2. Clip a job posting to create job application
3. Click the 📤 "Export to Linear" button
4. Extension creates main task + 16 subtasks with job data
5. Automatically opens the created task in Linear

## 🛣️ Roadmap / TODOs

### 🔶 High Priority (Next 1–2 weeks)
- [ ] Build/dev experience
  - [x] Add `build:dev` (watch + fast incremental builds) and `build:prod` (minify, sourcemaps) scripts
- [x] Cross-platform `clean` using `rimraf` instead of `rm -rf`
- [x] Ensure no top‑level `await` in IIFE bundles; consider switching popup to `esm` if needed
- [x] Generate source maps for `background.js`, `content.js`, `popup.js`
- [ ] Settings UX & validation
  - [x] Add inline validation for `BACKEND_API_BASE`, `GROQ_API_KEY`, `LINEAR_API_KEY`, `LINEAR_TEAM_ID`
- [x] Mask API keys in UI with “show/hide” toggle
- [x] “Test connection” actions for Groq and Linear (with success/error feedback)
- [x] Export/import settings as JSON (optional encryption)
- [ ] Linear integration hardening
  - [x] Prevent duplicate issue creation by storing mapping `job_application_id -> linear_issue_id`
- [x] Allow selecting project/labels during export (from cached Linear metadata)
- [x] Retry with backoff on 429/5xx; surface partial failures per subtask
- [x] Add cancel/export-in-progress guard
- [ ] Permissions minimization
  - [x] Replace `<all_urls>` with `optional_host_permissions` + on‑demand injection using `activeTab`
- [x] Document rationale for any non-optional host permissions
- [ ] Privacy & data handling
  - [x] Explicit consent toggle before sending data to Groq/Linear
- [x] Redact PII in logs and UI console

### 🟡 Medium Priority (2–4 weeks)
- [ ] Performance
  - [ ] Reduce `popup.js` bundle size (tree‑shaking, code‑split non‑critical features)
  - [ ] Lazy‑load report generation and PDF parsing modules
  - [ ] Debounce UI console rendering and DOM updates on typing
- [ ] Database
  - [x] Add schema versioning/migrations (v1 -> v2)
- [x] Add per‑table export/import; space usage diagnostics
  - [ ] Optionally encrypt IndexedDB payloads (user‑provided key)
- [ ] PDF/resume
  - [ ] Drag‑and‑drop resume upload
  - [ ] Local OCR fallback (Tesseract) when Groq unavailable (opt‑in)
- [ ] UI/UX
  - [ ] Keyboard navigation, ARIA roles, and focus management across sections
  - [ ] Persistent panel collapse/expand state; “collapse/expand all” controls
  - [ ] Non‑blocking native notifications (auto‑dismiss, consistent styling)
- [ ] Stability
  - [ ] Global error boundary for popup; user‑friendly recovery actions
  - [ ] Background worker health ping + auto‑restart hints in console

### 🔵 Testing & Quality
- [ ] Linting/formatting
  - [ ] Add ESLint + Prettier with TypeScript rules; CI enforcement
- [ ] Unit tests
  - [ ] Jest tests for: URL canonicalization, repository CRUD, Linear client mapping
- [ ] E2E
  - [ ] Playwright-based extension tests (basic clip, settings, export to Linear)
- [ ] CI/CD
  - [ ] GitHub Actions workflow: install, build, lint, test, artifact upload (`dist/extension`)
  - [ ] Version bump + changelog generation on release tags

### 🧩 Internationalization
- [ ] i18n coverage audit to ensure all UI strings are in locale files
- [ ] Add missing ARIA/notifications/messages to translations
- [ ] Optional additional languages (DE, ES) if contributors available

### 🔐 Security & Compliance
- [x] CSP review for popup and any injected content (no inline scripts/styles)
- [x] Sanitize/escape any rendered markdown/HTML (e.g., DOMPurify) before preview
- [x] Secrets handling policy in docs; never log keys; mask in crash reports
- [ ] Threat model doc for data flows (clip → storage → LLM/Linear)

### 🌐 Browser Compatibility & Distribution
- [ ] Firefox port (MV3 module worker support or MV2 compatibility via build flag)
- [ ] Edge store packaging and metadata prep
- [ ] Chrome Web Store: listing assets, policy-compliant privacy page, versioning plan

### 📄 Documentation
- [ ] Contributor guide (setup, scripts, coding standards, testing)
- [ ] Architecture doc (modules, data flow, integration points)
- [ ] User guide with screenshots/GIFs for key flows (clip, report, Linear export)

### 🧪 Nice-to-have Enhancements
- [ ] Real‑time streaming preview improvements (pause/resume, token counter)
- [ ] Clipboard: copy structured JSON and minimal markdown variants
- [ ] In‑product tips/help panel with contextual guidance
