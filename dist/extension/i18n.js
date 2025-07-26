// Internationalization Manager for JobOps Clipper
// Handles language detection, translation loading, and dynamic content translation
class I18nManager {
    constructor() {
        this.currentLanguage = 'en';
        this.translations = new Map();
        this.isInitialized = false;
        this.initializationPromise = null;
        // Free translation API endpoints (using LibreTranslate as it's free and open source)
        this.TRANSLATION_API_URL = 'https://libretranslate.de/translate';
        this.FALLBACK_API_URL = 'https://translate.argosopentech.com/translate';
        this.detectBrowserLanguage();
    }
    /**
     * Initialize the i18n manager by loading all translation files
     */
    async initialize() {
        if (this.isInitialized) {
            return;
        }
        if (this.initializationPromise) {
            return this.initializationPromise;
        }
        this.initializationPromise = this.loadAllTranslations();
        await this.initializationPromise;
        this.isInitialized = true;
    }
    /**
     * Detect browser language and set initial language
     */
    detectBrowserLanguage() {
        const browserLang = navigator.language.toLowerCase();
        const langCode = browserLang.split('-')[0];
        if (this.isSupportedLanguage(langCode)) {
            this.currentLanguage = langCode;
        }
        else {
            this.currentLanguage = 'en'; // Default to English
        }
    }
    /**
     * Check if a language code is supported
     */
    isSupportedLanguage(lang) {
        return ['en', 'nl', 'fr', 'tr'].includes(lang);
    }
    /**
     * Load all translation files
     */
    async loadAllTranslations() {
        const languages = ['en', 'nl', 'fr', 'tr'];
        const loadPromises = languages.map(async (lang) => {
            try {
                const response = await fetch(chrome.runtime.getURL(`src/locales/${lang}.json`));
                if (!response.ok) {
                    throw new Error(`Failed to load ${lang} translation: ${response.statusText}`);
                }
                const translationData = await response.json();
                this.translations.set(lang, translationData);
            }
            catch (error) {
                console.error(`Error loading ${lang} translation:`, error);
                // If loading fails, create a fallback with English content
                if (lang !== 'en') {
                    const englishData = this.translations.get('en');
                    if (englishData) {
                        this.translations.set(lang, englishData);
                    }
                }
            }
        });
        await Promise.all(loadPromises);
    }
    /**
     * Get current language
     */
    getCurrentLanguage() {
        return this.currentLanguage;
    }
    /**
     * Get supported languages
     */
    getSupportedLanguages() {
        const languages = [];
        this.translations.forEach((data, code) => {
            languages.push(data.language);
        });
        return languages;
    }
    /**
     * Change the current language
     */
    async setLanguage(lang) {
        if (!this.isSupportedLanguage(lang)) {
            throw new Error(`Unsupported language: ${lang}`);
        }
        if (!this.translations.has(lang)) {
            throw new Error(`Translation not loaded for language: ${lang}`);
        }
        this.currentLanguage = lang;
        // Save language preference
        chrome.storage.sync.set({ jobops_language: lang }, () => {
            console.log(`Language preference saved: ${lang}`);
        });
        // Trigger UI update
        this.updateUI();
    }
    /**
     * Load saved language preference
     */
    async loadSavedLanguage() {
        return new Promise((resolve) => {
            chrome.storage.sync.get(['jobops_language'], (result) => {
                const savedLang = result.jobops_language;
                if (savedLang && this.isSupportedLanguage(savedLang)) {
                    this.currentLanguage = savedLang;
                }
                resolve();
            });
        });
    }
    /**
     * Get translation for a key
     */
    t(key, section = 'ui') {
        const translation = this.translations.get(this.currentLanguage);
        if (!translation) {
            console.warn(`Translation not found for language: ${this.currentLanguage}`);
            return key;
        }
        const sectionData = translation[section];
        if (!sectionData || typeof sectionData !== 'object') {
            console.warn(`Translation section not found: ${section}`);
            return key;
        }
        // Type guard to ensure sectionData is a Record<string, string>
        if (section === 'language') {
            console.warn(`Cannot access language config with t() method`);
            return key;
        }
        const recordData = sectionData;
        const value = recordData[key];
        if (!value) {
            console.warn(`Translation key not found: ${section}.${key}`);
            return key;
        }
        return value;
    }
    /**
     * Translate dynamic content using free translation API
     */
    async translateContent(text, targetLang) {
        if (!text || text.trim() === '') {
            return text;
        }
        const targetLanguage = targetLang || this.currentLanguage;
        // Don't translate if target language is English (source language)
        if (targetLanguage === 'en') {
            return text;
        }
        try {
            // Try primary translation API
            const translatedText = await this.callTranslationAPI(text, targetLanguage);
            if (translatedText) {
                return translatedText;
            }
        }
        catch (error) {
            console.warn('Primary translation API failed, trying fallback:', error);
        }
        try {
            // Try fallback translation API
            const translatedText = await this.callTranslationAPI(text, targetLanguage, true);
            if (translatedText) {
                return translatedText;
            }
        }
        catch (error) {
            console.error('All translation APIs failed:', error);
        }
        // Return original text if translation fails
        return text;
    }
    /**
     * Call translation API
     */
    async callTranslationAPI(text, targetLang, useFallback = false) {
        const apiUrl = useFallback ? this.FALLBACK_API_URL : this.TRANSLATION_API_URL;
        const response = await fetch(apiUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                q: text,
                source: 'en',
                target: targetLang,
                format: 'text'
            })
        });
        if (!response.ok) {
            throw new Error(`Translation API error: ${response.status} ${response.statusText}`);
        }
        const data = await response.json();
        return data.translatedText || text;
    }
    /**
     * Update all UI elements with current language
     */
    updateUI() {
        // Update section headers
        this.updateSectionHeaders();
        // Update placeholders
        this.updatePlaceholders();
        // Update labels
        this.updateLabels();
        // Update buttons
        this.updateButtons();
        // Update aria labels
        this.updateAriaLabels();
        // Update console messages
        this.updateConsoleMessages();
    }
    /**
     * Update section headers
     */
    updateSectionHeaders() {
        const sections = [
            { selector: '[data-toggle="properties-content"] .section-title', key: 'properties' },
            { selector: '[data-section="position-details"] .section-title', key: 'positionDetails' },
            { selector: '[data-section="job-requirements"] .section-title', key: 'jobRequirements' },
            { selector: '[data-section="company-information"] .section-title', key: 'companyInformation' },
            { selector: '[data-section="skills-matrix"] .section-title', key: 'skillsMatrix' },
            { selector: '[data-section="application-materials"] .section-title', key: 'applicationMaterials' },
            { selector: '[data-section="interview-schedule"] .section-title', key: 'interviewSchedule' },
            { selector: '[data-section="interview-preparation"] .section-title', key: 'interviewPreparation' },
            { selector: '[data-section="communication-log"] .section-title', key: 'communicationLog' },
            { selector: '[data-section="key-contacts"] .section-title', key: 'keyContacts' },
            { selector: '[data-section="interview-feedback"] .section-title', key: 'interviewFeedback' },
            { selector: '[data-section="offer-details"] .section-title', key: 'offerDetails' },
            { selector: '[data-section="rejection-analysis"] .section-title', key: 'rejectionAnalysis' },
            { selector: '[data-section="privacy-policy"] .section-title', key: 'privacyPolicy' },
            { selector: '[data-section="lessons-learned"] .section-title', key: 'lessonsLearned' },
            { selector: '[data-section="performance-metrics"] .section-title', key: 'performanceMetrics' },
            { selector: '[data-section="advisor-review"] .section-title', key: 'advisorReview' },
            { selector: '[data-section="application-summary"] .section-title', key: 'applicationSummary' },
            { selector: '[data-toggle="markdown-content"] .section-title', key: 'markdownPreview' },
            { selector: '[data-toggle="realtime-content"] .section-title', key: 'realtimeResponse' },
            { selector: '.console-title .section-title', key: 'debugConsole' }
        ];
        sections.forEach(({ selector, key }) => {
            const element = document.querySelector(selector);
            if (element && element.textContent !== null) {
                element.textContent = this.t(key);
            }
        });
    }
    /**
     * Update input placeholders
     */
    updatePlaceholders() {
        const placeholders = [
            { id: 'prop-title', key: 'title' },
            { id: 'prop-url', key: 'sourceUrl' },
            { id: 'prop-author', key: 'author' },
            { id: 'prop-published', key: 'published' },
            { id: 'prop-created', key: 'created' },
            { id: 'prop-description', key: 'description' },
            { id: 'prop-tags', key: 'tags' },
            { id: 'prop-location', key: 'location' },
            { id: 'position-summary', key: 'positionSummary' },
            { id: 'requirements-summary', key: 'requirementsSummary' },
            { id: 'company-summary', key: 'companySummary' },
            { id: 'skills-assessment', key: 'skillsAssessment' },
            { id: 'materials-summary', key: 'materialsSummary' },
            { id: 'interview-details', key: 'interviewDetails' },
            { id: 'preparation-summary', key: 'preparationSummary' },
            { id: 'communication-summary', key: 'communicationSummary' },
            { id: 'contacts-summary', key: 'contactsSummary' },
            { id: 'feedback-summary', key: 'feedbackSummary' },
            { id: 'offer-summary', key: 'offerSummary' },
            { id: 'rejection-summary', key: 'rejectionSummary' },
            { id: 'privacy-summary', key: 'privacySummary' },
            { id: 'lessons-summary', key: 'lessonsSummary' },
            { id: 'metrics-summary', key: 'metricsSummary' },
            { id: 'advisor-summary', key: 'advisorSummary' },
            { id: 'overall-summary', key: 'overallSummary' },
            { id: 'markdown-editor', key: 'markdownEditor' }
        ];
        placeholders.forEach(({ id, key }) => {
            const element = document.getElementById(id);
            if (element) {
                element.placeholder = this.t(key, 'placeholders');
            }
        });
        // Update realtime response placeholder
        const realtimeResponse = document.getElementById('realtime-response');
        if (realtimeResponse) {
            realtimeResponse.setAttribute('placeholder', this.t('aiResponse', 'placeholders'));
        }
    }
    /**
     * Update labels
     */
    updateLabels() {
        const labels = [
            { selector: 'label[for="position-summary"]', key: 'positionSummary' },
            { selector: 'label[for="requirements-summary"]', key: 'requirementsSummary' },
            { selector: 'label[for="company-summary"]', key: 'companySummary' },
            { selector: 'label[for="skills-assessment"]', key: 'skillsAssessment' },
            { selector: 'label[for="materials-summary"]', key: 'materialsSummary' },
            { selector: 'label[for="interview-details"]', key: 'interviewDetails' },
            { selector: 'label[for="preparation-summary"]', key: 'preparationSummary' },
            { selector: 'label[for="communication-summary"]', key: 'communicationSummary' },
            { selector: 'label[for="contacts-summary"]', key: 'contactsSummary' },
            { selector: 'label[for="feedback-summary"]', key: 'feedbackSummary' },
            { selector: 'label[for="offer-summary"]', key: 'offerSummary' },
            { selector: 'label[for="rejection-summary"]', key: 'rejectionSummary' },
            { selector: 'label[for="privacy-summary"]', key: 'privacySummary' },
            { selector: 'label[for="lessons-summary"]', key: 'lessonsSummary' },
            { selector: 'label[for="metrics-summary"]', key: 'metricsSummary' },
            { selector: 'label[for="advisor-summary"]', key: 'advisorSummary' },
            { selector: 'label[for="overall-summary"]', key: 'overallSummary' }
        ];
        labels.forEach(({ selector, key }) => {
            const element = document.querySelector(selector);
            if (element) {
                element.textContent = this.t(key, 'labels');
            }
        });
    }
    /**
     * Update button text
     */
    updateButtons() {
        // Action buttons should only show icons, not text
        const actionButtons = [
            { id: 'copy-markdown', key: 'copy' },
            { id: 'generate-report', key: 'generateReport' },
            { id: 'settings', key: 'settings' },
            { id: 'language-toggle', key: 'languageSelector' }
        ];
        // Control buttons can have text
        const controlButtons = [
            { id: 'stop-generation', key: 'stop' },
            { id: 'copy-realtime', key: 'copy' },
            { id: 'clear-console', key: 'clear' }
        ];
        // Update action buttons - preserve icons only
        actionButtons.forEach(({ id, key }) => {
            const element = document.getElementById(id);
            if (element && element.textContent) {
                const icon = element.textContent.match(/[^\u0000-\u007F]/g)?.join('') || '';
                element.textContent = icon; // Keep only the icon
            }
        });
        // Update control buttons - keep icon + text
        controlButtons.forEach(({ id, key }) => {
            const element = document.getElementById(id);
            if (element && element.textContent) {
                const icon = element.textContent.match(/[^\u0000-\u007F]/g)?.join('') || '';
                element.textContent = `${icon} ${this.t(key, 'buttons')}`.trim();
            }
        });
    }
    /**
     * Update aria labels
     */
    updateAriaLabels() {
        const ariaLabels = [
            { id: 'copy-markdown', key: 'copyToClipboard' },
            { id: 'generate-report', key: 'generateReport' },
            { id: 'theme-toggle', key: 'toggleTheme' },
            { id: 'settings', key: 'settings' },
            { id: 'clear-console', key: 'clearConsole' }
        ];
        ariaLabels.forEach(({ id, key }) => {
            const element = document.getElementById(id);
            if (element) {
                element.setAttribute('aria-label', this.t(key, 'ariaLabels'));
            }
        });
    }
    /**
     * Update console messages (this would be called when logging)
     */
    updateConsoleMessages() {
        // Console messages are updated dynamically when logging
        // This method can be used to update any static console messages
    }
    /**
     * Get notification message
     */
    getNotificationMessage(key) {
        return this.t(key, 'notifications');
    }
    /**
     * Get console message
     */
    getConsoleMessage(key) {
        return this.t(key, 'console');
    }
    /**
     * Translate dynamic content in real-time
     */
    async translateDynamicContent() {
        // Get all textarea and input elements with content
        const textElements = document.querySelectorAll('textarea, input[type="text"]');
        for (const element of textElements) {
            const textElement = element;
            if (textElement.value && textElement.value.trim() !== '') {
                const originalText = textElement.value;
                const translatedText = await this.translateContent(originalText);
                if (translatedText !== originalText) {
                    textElement.value = translatedText;
                }
            }
        }
        // Update any other dynamic content areas
        const dynamicAreas = document.querySelectorAll('.realtime-response, .markdown-editor');
        for (const area of dynamicAreas) {
            if (area.textContent && area.textContent.trim() !== '') {
                const originalText = area.textContent;
                const translatedText = await this.translateContent(originalText);
                if (translatedText !== originalText) {
                    area.textContent = translatedText;
                }
            }
        }
    }
}
// Create singleton instance
export const i18n = new I18nManager();
