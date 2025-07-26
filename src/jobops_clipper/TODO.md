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
