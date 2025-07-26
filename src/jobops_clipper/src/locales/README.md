# Internationalization (i18n) System

This directory contains the internationalization configuration for the JobOps Clipper extension.

## Supported Languages

- **English (US)** - `en.json` 🇺🇸
- **Dutch (Belgium)** - `nl.json` 🇧🇪
- **French (Belgium)** - `fr.json` 🇧🇪
- **Turkish (Turkey)** - `tr.json` 🇹🇷

## Language Detection

The system automatically detects the user's browser language and sets the initial language accordingly. If the browser language is not supported, it defaults to English.

## Language Switching

Users can change the language by clicking the language selector button (🌐) in the action buttons bar. This opens a dropdown with all supported languages, showing flags and country names.

## Translation Structure

Each language file contains the following sections:

- **language**: Language metadata (code, name, flag, country)
- **ui**: User interface text (section headers, titles)
- **placeholders**: Input field placeholder text
- **labels**: Form labels
- **buttons**: Button text
- **ariaLabels**: Accessibility labels
- **notifications**: Notification messages
- **console**: Console log messages
- **languages**: Language names in different languages

## Dynamic Content Translation

The system includes automatic translation of dynamic content using free translation APIs:

1. **LibreTranslate** (primary) - https://libretranslate.de/
2. **Argos Translate** (fallback) - https://translate.argosopentech.com/

When a user changes the language, all existing content in text areas and input fields is automatically translated to the new language.

## Adding New Languages

To add a new language:

1. Create a new JSON file in this directory (e.g., `de.json` for German)
2. Copy the structure from `en.json` and translate all values
3. Update the `SupportedLanguage` type in `i18n.ts`
4. Add the language to the `getSupportedLanguages()` method
5. Update the language dropdown in `popup.html`

## Technical Implementation

- **i18n.ts**: Main internationalization manager
- **popup.ts**: Integration with the UI
- **popup.html**: Language selector dropdown
- **popup.css**: Styling for language selector

## Storage

Language preferences are stored in Chrome's sync storage under the key `jobops_language` and persist across browser sessions.

## API Permissions

The extension requires permissions to access translation APIs:
- `https://libretranslate.de/*`
- `https://translate.argosopentech.com/*`

These are added to the `host_permissions` in `manifest.json`. 