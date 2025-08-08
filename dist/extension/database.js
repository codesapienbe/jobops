// Database schema and operations for JobOps Clipper
// Uses SQLite for local storage with proper table relationships
export class JobOpsDatabase {
    constructor() {
        this.db = null;
        this.dbName = 'JobOpsDatabase';
        this.dbVersion = 2;
        this.allTables = [
            'job_applications',
            'position_details',
            'job_requirements',
            'company_information',
            'skills_matrix',
            'skill_assessments',
            'application_materials',
            'interview_schedule',
            'interview_preparation',
            'communication_log',
            'key_contacts',
            'interview_feedback',
            'offer_details',
            'rejection_analysis',
            'privacy_policy',
            'lessons_learned',
            'performance_metrics',
            'advisor_review'
        ];
        // Encryption state
        this.encryptionEnabled = false;
        this.cryptoKey = null;
        this.pbkdf2Iterations = 250000;
        this.initializeDatabase();
    }
    // Public API to configure encryption for the session
    async configureEncryption(enabled, passphrase) {
        this.encryptionEnabled = enabled;
        if (!enabled) {
            this.cryptoKey = null;
            return;
        }
        if (!passphrase || passphrase.trim().length < 8) {
            throw new Error('Passphrase must be at least 8 characters');
        }
        const salt = await this.getOrCreateSalt();
        this.cryptoKey = await this.deriveKey(passphrase, salt);
    }
    isEncryptionEnabled() {
        return this.encryptionEnabled && !!this.cryptoKey;
    }
    async getOrCreateSalt() {
        const existing = await this.getMetadata('encryption_salt');
        if (existing && existing.value) {
            return this.base64ToBytes(existing.value);
        }
        const salt = crypto.getRandomValues(new Uint8Array(16));
        await this.setMetadata('encryption_salt', this.bytesToBase64(salt));
        return salt;
    }
    async getMetadata(key) {
        if (!this.db)
            throw new Error('Database not initialized');
        return new Promise((resolve, reject) => {
            if (!this.db.objectStoreNames.contains('metadata')) {
                resolve(null);
                return;
            }
            const tx = this.db.transaction(['metadata'], 'readonly');
            const store = tx.objectStore('metadata');
            const req = store.get(key);
            req.onsuccess = () => resolve(req.result || null);
            req.onerror = () => reject(req.error);
        });
    }
    async setMetadata(key, value) {
        if (!this.db)
            throw new Error('Database not initialized');
        return new Promise((resolve, reject) => {
            if (!this.db.objectStoreNames.contains('metadata')) {
                // create store is only allowed in onupgradeneeded; ignore here
                resolve();
                return;
            }
            const tx = this.db.transaction(['metadata'], 'readwrite');
            const store = tx.objectStore('metadata');
            const now = new Date().toISOString();
            const req = store.put({ key, value, updated_at: now });
            req.onsuccess = () => resolve();
            req.onerror = () => reject(req.error);
        });
    }
    async deriveKey(passphrase, salt) {
        const enc = new TextEncoder();
        const baseKey = await crypto.subtle.importKey('raw', enc.encode(passphrase), 'PBKDF2', false, ['deriveKey']);
        return crypto.subtle.deriveKey({ name: 'PBKDF2', salt, iterations: this.pbkdf2Iterations, hash: 'SHA-256' }, baseKey, { name: 'AES-GCM', length: 256 }, false, ['encrypt', 'decrypt']);
    }
    async encryptPayload(obj) {
        if (!this.cryptoKey)
            throw new Error('Encryption key not configured');
        const ivBytes = crypto.getRandomValues(new Uint8Array(12));
        const enc = new TextEncoder();
        const plaintext = enc.encode(JSON.stringify(obj));
        const ciphertext = await crypto.subtle.encrypt({ name: 'AES-GCM', iv: ivBytes }, this.cryptoKey, plaintext);
        return { iv: this.bytesToBase64(ivBytes), data: this.bytesToBase64(new Uint8Array(ciphertext)), alg: 'AES-GCM', v: 1 };
    }
    async decryptPayload(encBlob) {
        if (!this.cryptoKey)
            throw new Error('Encryption key not configured');
        const iv = this.base64ToBytes(encBlob.iv);
        const data = this.base64ToBytes(encBlob.data);
        const plaintext = await crypto.subtle.decrypt({ name: 'AES-GCM', iv }, this.cryptoKey, data);
        const dec = new TextDecoder();
        return JSON.parse(dec.decode(new Uint8Array(plaintext)));
    }
    bytesToBase64(bytes) {
        let binary = '';
        for (let i = 0; i < bytes.byteLength; i++)
            binary += String.fromCharCode(bytes[i]);
        return btoa(binary);
    }
    base64ToBytes(b64) {
        const binary = atob(b64);
        const bytes = new Uint8Array(binary.length);
        for (let i = 0; i < binary.length; i++)
            bytes[i] = binary.charCodeAt(i);
        return bytes;
    }
    // Split record into index fields (plaintext) and payload (to encrypt)
    splitForEncryption(tableName, record) {
        const indexFields = new Set(['id', 'created_at', 'updated_at']);
        if ('job_application_id' in record)
            indexFields.add('job_application_id');
        if (tableName === 'skill_assessments' && 'skills_matrix_id' in record)
            indexFields.add('skills_matrix_id');
        if (tableName === 'job_applications') {
            if ('canonical_url' in record)
                indexFields.add('canonical_url');
            if ('status' in record)
                indexFields.add('status');
        }
        const indexPart = {};
        const payload = {};
        for (const [k, v] of Object.entries(record)) {
            if (indexFields.has(k))
                indexPart[k] = v;
            else
                payload[k] = v;
        }
        return { indexPart, payload };
    }
    async prepareRecordForStore(tableName, record) {
        if (!this.isEncryptionEnabled())
            return record;
        const { indexPart, payload } = this.splitForEncryption(tableName, record);
        const enc = await this.encryptPayload(payload);
        return { ...indexPart, __encrypted: true, __enc: enc };
    }
    async reconstructRecordFromStore(tableName, stored) {
        if (!stored || !stored.__encrypted)
            return stored;
        if (!this.isEncryptionEnabled()) {
            throw new Error('Encryption is enabled for data but no key configured. Please set passphrase in settings.');
        }
        const decrypted = await this.decryptPayload(stored.__enc);
        const { __encrypted, __enc, ...indexPart } = stored;
        return { ...indexPart, ...decrypted };
    }
    async initializeDatabase() {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open(this.dbName, this.dbVersion);
            request.onerror = () => {
                console.error('Failed to open database:', request.error);
                reject(request.error);
            };
            request.onsuccess = () => {
                this.db = request.result;
                console.log('Database opened successfully');
                resolve();
            };
            request.onupgradeneeded = (event) => {
                const db = event.target.result;
                const oldVersion = event.oldVersion || 0;
                this.createTables(db);
                // Migrations for v2
                if (oldVersion < 2) {
                    // Metadata store for schema tracking
                    if (!db.objectStoreNames.contains('metadata')) {
                        const meta = db.createObjectStore('metadata', { keyPath: 'key' });
                        try {
                            meta.put({ key: 'schemaVersion', value: 2, updated_at: new Date().toISOString() });
                        }
                        catch { }
                    }
                    // Add updated_at indexes to improve diagnostics/queries
                    const addUpdatedAtIndex = (storeName) => {
                        if (db.objectStoreNames.contains(storeName)) {
                            const store = event.currentTarget.transaction?.objectStore(storeName) || db.transaction([storeName], 'versionchange').objectStore(storeName);
                            try {
                                store.createIndex('updated_at', 'updated_at', { unique: false });
                            }
                            catch { }
                        }
                    };
                    this.allTables.forEach(addUpdatedAtIndex);
                }
            };
        });
    }
    createTables(db) {
        // Main job application table
        if (!db.objectStoreNames.contains('job_applications')) {
            const jobApplicationsStore = db.createObjectStore('job_applications', { keyPath: 'id' });
            jobApplicationsStore.createIndex('canonical_url', 'canonical_url', { unique: true });
            jobApplicationsStore.createIndex('status', 'status', { unique: false });
            jobApplicationsStore.createIndex('created_at', 'created_at', { unique: false });
            jobApplicationsStore.createIndex('updated_at', 'updated_at', { unique: false });
        }
        // Position details table
        if (!db.objectStoreNames.contains('position_details')) {
            const positionDetailsStore = db.createObjectStore('position_details', { keyPath: 'id' });
            positionDetailsStore.createIndex('job_application_id', 'job_application_id', { unique: false });
            positionDetailsStore.createIndex('updated_at', 'updated_at', { unique: false });
        }
        // Job requirements table
        if (!db.objectStoreNames.contains('job_requirements')) {
            const jobRequirementsStore = db.createObjectStore('job_requirements', { keyPath: 'id' });
            jobRequirementsStore.createIndex('job_application_id', 'job_application_id', { unique: false });
            jobRequirementsStore.createIndex('updated_at', 'updated_at', { unique: false });
        }
        // Company information table
        if (!db.objectStoreNames.contains('company_information')) {
            const companyInformationStore = db.createObjectStore('company_information', { keyPath: 'id' });
            companyInformationStore.createIndex('job_application_id', 'job_application_id', { unique: false });
            companyInformationStore.createIndex('updated_at', 'updated_at', { unique: false });
        }
        // Skills matrix table
        if (!db.objectStoreNames.contains('skills_matrix')) {
            const skillsMatrixStore = db.createObjectStore('skills_matrix', { keyPath: 'id' });
            skillsMatrixStore.createIndex('job_application_id', 'job_application_id', { unique: false });
            skillsMatrixStore.createIndex('updated_at', 'updated_at', { unique: false });
        }
        // Skill assessments table
        if (!db.objectStoreNames.contains('skill_assessments')) {
            const skillAssessmentsStore = db.createObjectStore('skill_assessments', { keyPath: 'id' });
            skillAssessmentsStore.createIndex('skills_matrix_id', 'skills_matrix_id', { unique: false });
            skillAssessmentsStore.createIndex('updated_at', 'updated_at', { unique: false });
        }
        // Application materials table
        if (!db.objectStoreNames.contains('application_materials')) {
            const applicationMaterialsStore = db.createObjectStore('application_materials', { keyPath: 'id' });
            applicationMaterialsStore.createIndex('job_application_id', 'job_application_id', { unique: false });
            applicationMaterialsStore.createIndex('updated_at', 'updated_at', { unique: false });
        }
        // Interview schedule table
        if (!db.objectStoreNames.contains('interview_schedule')) {
            const interviewScheduleStore = db.createObjectStore('interview_schedule', { keyPath: 'id' });
            interviewScheduleStore.createIndex('job_application_id', 'job_application_id', { unique: false });
            interviewScheduleStore.createIndex('updated_at', 'updated_at', { unique: false });
        }
        // Interview preparation table
        if (!db.objectStoreNames.contains('interview_preparation')) {
            const interviewPreparationStore = db.createObjectStore('interview_preparation', { keyPath: 'id' });
            interviewPreparationStore.createIndex('job_application_id', 'job_application_id', { unique: false });
            interviewPreparationStore.createIndex('updated_at', 'updated_at', { unique: false });
        }
        // Communication log table
        if (!db.objectStoreNames.contains('communication_log')) {
            const communicationLogStore = db.createObjectStore('communication_log', { keyPath: 'id' });
            communicationLogStore.createIndex('job_application_id', 'job_application_id', { unique: false });
            communicationLogStore.createIndex('updated_at', 'updated_at', { unique: false });
        }
        // Key contacts table
        if (!db.objectStoreNames.contains('key_contacts')) {
            const keyContactsStore = db.createObjectStore('key_contacts', { keyPath: 'id' });
            keyContactsStore.createIndex('job_application_id', 'job_application_id', { unique: false });
            keyContactsStore.createIndex('updated_at', 'updated_at', { unique: false });
        }
        // Interview feedback table
        if (!db.objectStoreNames.contains('interview_feedback')) {
            const interviewFeedbackStore = db.createObjectStore('interview_feedback', { keyPath: 'id' });
            interviewFeedbackStore.createIndex('job_application_id', 'job_application_id', { unique: false });
            interviewFeedbackStore.createIndex('updated_at', 'updated_at', { unique: false });
        }
        // Offer details table
        if (!db.objectStoreNames.contains('offer_details')) {
            const offerDetailsStore = db.createObjectStore('offer_details', { keyPath: 'id' });
            offerDetailsStore.createIndex('job_application_id', 'job_application_id', { unique: false });
            offerDetailsStore.createIndex('updated_at', 'updated_at', { unique: false });
        }
        // Rejection analysis table
        if (!db.objectStoreNames.contains('rejection_analysis')) {
            const rejectionAnalysisStore = db.createObjectStore('rejection_analysis', { keyPath: 'id' });
            rejectionAnalysisStore.createIndex('job_application_id', 'job_application_id', { unique: false });
            rejectionAnalysisStore.createIndex('updated_at', 'updated_at', { unique: false });
        }
        // Privacy policy table
        if (!db.objectStoreNames.contains('privacy_policy')) {
            const privacyPolicyStore = db.createObjectStore('privacy_policy', { keyPath: 'id' });
            privacyPolicyStore.createIndex('job_application_id', 'job_application_id', { unique: false });
            privacyPolicyStore.createIndex('updated_at', 'updated_at', { unique: false });
        }
        // Lessons learned table
        if (!db.objectStoreNames.contains('lessons_learned')) {
            const lessonsLearnedStore = db.createObjectStore('lessons_learned', { keyPath: 'id' });
            lessonsLearnedStore.createIndex('job_application_id', 'job_application_id', { unique: false });
            lessonsLearnedStore.createIndex('updated_at', 'updated_at', { unique: false });
        }
        // Performance metrics table
        if (!db.objectStoreNames.contains('performance_metrics')) {
            const performanceMetricsStore = db.createObjectStore('performance_metrics', { keyPath: 'id' });
            performanceMetricsStore.createIndex('job_application_id', 'job_application_id', { unique: false });
            performanceMetricsStore.createIndex('updated_at', 'updated_at', { unique: false });
        }
        // Advisor review table
        if (!db.objectStoreNames.contains('advisor_review')) {
            const advisorReviewStore = db.createObjectStore('advisor_review', { keyPath: 'id' });
            advisorReviewStore.createIndex('job_application_id', 'job_application_id', { unique: false });
            advisorReviewStore.createIndex('updated_at', 'updated_at', { unique: false });
        }
    }
    // Check if job application exists by canonical URL
    async checkJobApplicationExists(canonicalUrl) {
        return new Promise((resolve, reject) => {
            if (!this.db) {
                reject(new Error('Database not initialized'));
                return;
            }
            const transaction = this.db.transaction(['job_applications'], 'readonly');
            const store = transaction.objectStore('job_applications');
            const index = store.index('canonical_url');
            const request = index.get(canonicalUrl);
            request.onsuccess = async () => {
                const stored = request.result || null;
                if (!stored) {
                    resolve(null);
                    return;
                }
                try {
                    const rec = await this.reconstructRecordFromStore('job_applications', stored);
                    resolve(rec || null);
                }
                catch (e) {
                    reject(e);
                }
            };
            request.onerror = () => {
                reject(request.error);
            };
        });
    }
    // Create new job application
    async createJobApplication(data) {
        return new Promise((resolve, reject) => {
            if (!this.db) {
                reject(new Error('Database not initialized'));
                return;
            }
            const id = this.generateId();
            const now = new Date().toISOString();
            const record = {
                ...data,
                id,
                created_at: now,
                updated_at: now
            };
            const transaction = this.db.transaction(['job_applications'], 'readwrite');
            const store = transaction.objectStore('job_applications');
            (async () => {
                try {
                    const prepared = await this.prepareRecordForStore('job_applications', record);
                    const request = store.add(prepared);
                    request.onsuccess = () => resolve(id);
                    request.onerror = () => reject(request.error);
                }
                catch (e) {
                    reject(e);
                }
            })();
        });
    }
    // Get job application by ID
    async getJobApplication(id) {
        return new Promise((resolve, reject) => {
            if (!this.db) {
                reject(new Error('Database not initialized'));
                return;
            }
            const transaction = this.db.transaction(['job_applications'], 'readonly');
            const store = transaction.objectStore('job_applications');
            const request = store.get(id);
            request.onsuccess = async () => {
                const stored = request.result || null;
                if (!stored) {
                    resolve(null);
                    return;
                }
                try {
                    const rec = await this.reconstructRecordFromStore('job_applications', stored);
                    resolve(rec || null);
                }
                catch (e) {
                    reject(e);
                }
            };
            request.onerror = () => {
                reject(request.error);
            };
        });
    }
    // Update job application
    async updateJobApplication(id, data) {
        return new Promise((resolve, reject) => {
            if (!this.db) {
                reject(new Error('Database not initialized'));
                return;
            }
            const transaction = this.db.transaction(['job_applications'], 'readwrite');
            const store = transaction.objectStore('job_applications');
            const getRequest = store.get(id);
            getRequest.onsuccess = () => {
                const existing = getRequest.result;
                if (!existing) {
                    reject(new Error('Job application not found'));
                    return;
                }
                (async () => {
                    try {
                        const fullExisting = await this.reconstructRecordFromStore('job_applications', existing);
                        const updated = {
                            ...fullExisting,
                            ...data,
                            updated_at: new Date().toISOString()
                        };
                        const prepared = await this.prepareRecordForStore('job_applications', updated);
                        const putRequest = store.put(prepared);
                        putRequest.onsuccess = () => resolve();
                        putRequest.onerror = () => reject(putRequest.error);
                    }
                    catch (e) {
                        reject(e);
                    }
                })();
            };
            getRequest.onerror = () => reject(getRequest.error);
        });
    }
    // Get all job applications
    async getAllJobApplications() {
        return new Promise((resolve, reject) => {
            if (!this.db) {
                reject(new Error('Database not initialized'));
                return;
            }
            const transaction = this.db.transaction(['job_applications'], 'readonly');
            const store = transaction.objectStore('job_applications');
            const request = store.getAll();
            request.onsuccess = async () => {
                try {
                    const list = request.result || [];
                    const decrypted = await Promise.all(list.map((r) => this.reconstructRecordFromStore('job_applications', r)));
                    resolve(decrypted);
                }
                catch (e) {
                    reject(e);
                }
            };
            request.onerror = () => {
                reject(request.error);
            };
        });
    }
    // Generic method to save section data
    async saveSectionData(tableName, data) {
        return new Promise((resolve, reject) => {
            if (!this.db) {
                reject(new Error('Database not initialized'));
                return;
            }
            const id = this.generateId();
            const now = new Date().toISOString();
            const record = {
                ...data,
                id,
                created_at: now,
                updated_at: now
            };
            const transaction = this.db.transaction([tableName], 'readwrite');
            const store = transaction.objectStore(tableName);
            (async () => {
                try {
                    const prepared = await this.prepareRecordForStore(tableName, record);
                    const request = store.add(prepared);
                    request.onsuccess = () => {
                        resolve(id);
                    };
                    request.onerror = () => {
                        reject(request.error);
                    };
                }
                catch (e) {
                    reject(e);
                }
            })();
        });
    }
    // Generic method to get section data by job application ID
    async getSectionDataByJobId(tableName, jobApplicationId) {
        return new Promise((resolve, reject) => {
            if (!this.db) {
                reject(new Error('Database not initialized'));
                return;
            }
            const transaction = this.db.transaction([tableName], 'readonly');
            const store = transaction.objectStore(tableName);
            const index = store.index('job_application_id');
            const request = index.getAll(jobApplicationId);
            request.onsuccess = async () => {
                try {
                    const list = request.result || [];
                    const decrypted = await Promise.all(list.map((r) => this.reconstructRecordFromStore(tableName, r)));
                    resolve(decrypted);
                }
                catch (e) {
                    reject(e);
                }
            };
            request.onerror = () => {
                reject(request.error);
            };
        });
    }
    // Generic method to update section data
    async updateSectionData(tableName, id, data) {
        return new Promise((resolve, reject) => {
            if (!this.db) {
                reject(new Error('Database not initialized'));
                return;
            }
            const transaction = this.db.transaction([tableName], 'readwrite');
            const store = transaction.objectStore(tableName);
            const getRequest = store.get(id);
            getRequest.onsuccess = () => {
                const existing = getRequest.result;
                if (!existing) {
                    reject(new Error('Record not found'));
                    return;
                }
                (async () => {
                    try {
                        const fullExisting = await this.reconstructRecordFromStore(tableName, existing);
                        const updated = {
                            ...fullExisting,
                            ...data,
                            updated_at: new Date().toISOString()
                        };
                        const prepared = await this.prepareRecordForStore(tableName, updated);
                        const putRequest = store.put(prepared);
                        putRequest.onsuccess = () => resolve();
                        putRequest.onerror = () => reject(putRequest.error);
                    }
                    catch (e) {
                        reject(e);
                    }
                })();
            };
            getRequest.onerror = () => reject(getRequest.error);
        });
    }
    // Per-table export
    async exportTable(tableName) {
        if (!this.db)
            throw new Error('Database not initialized');
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([tableName], 'readonly');
            const store = transaction.objectStore(tableName);
            const request = store.getAll();
            request.onsuccess = async () => {
                try {
                    const list = request.result || [];
                    const decrypted = await Promise.all(list.map((r) => this.reconstructRecordFromStore(tableName, r)));
                    resolve(decrypted);
                }
                catch (e) {
                    reject(e);
                }
            };
            request.onerror = () => reject(request.error);
        });
    }
    // Per-table import (append)
    async importTable(tableName, records) {
        if (!this.db)
            throw new Error('Database not initialized');
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([tableName], 'readwrite');
            const store = transaction.objectStore(tableName);
            (async () => {
                try {
                    for (const rec of records) {
                        const prepared = await this.prepareRecordForStore(tableName, rec);
                        store.put(prepared);
                    }
                    transaction.oncomplete = () => resolve();
                    transaction.onerror = () => reject(transaction.error);
                }
                catch (e) {
                    reject(e);
                }
            })();
        });
    }
    // Space usage diagnostics (approximate)
    async getSpaceUsage() {
        if (!this.db)
            throw new Error('Database not initialized');
        const results = [];
        for (const table of this.allTables) {
            const rows = await this.exportTable(table);
            const approxBytes = new TextEncoder().encode(JSON.stringify(rows)).length;
            results.push({ table, count: rows.length, approxBytes });
        }
        return results;
    }
    // Get complete job application with all sections
    async getCompleteJobApplication(jobApplicationId) {
        const jobApplication = await this.getJobApplication(jobApplicationId);
        if (!jobApplication) {
            throw new Error('Job application not found');
        }
        const [positionDetails, jobRequirements, companyInformation, skillsMatrix, applicationMaterials, interviewSchedule, interviewPreparation, communicationLog, keyContacts, interviewFeedback, offerDetails, rejectionAnalysis, privacyPolicy, lessonsLearned, performanceMetrics, advisorReview] = await Promise.all([
            this.getSectionDataByJobId('position_details', jobApplicationId),
            this.getSectionDataByJobId('job_requirements', jobApplicationId),
            this.getSectionDataByJobId('company_information', jobApplicationId),
            this.getSectionDataByJobId('skills_matrix', jobApplicationId),
            this.getSectionDataByJobId('application_materials', jobApplicationId),
            this.getSectionDataByJobId('interview_schedule', jobApplicationId),
            this.getSectionDataByJobId('interview_preparation', jobApplicationId),
            this.getSectionDataByJobId('communication_log', jobApplicationId),
            this.getSectionDataByJobId('key_contacts', jobApplicationId),
            this.getSectionDataByJobId('interview_feedback', jobApplicationId),
            this.getSectionDataByJobId('offer_details', jobApplicationId),
            this.getSectionDataByJobId('rejection_analysis', jobApplicationId),
            this.getSectionDataByJobId('privacy_policy', jobApplicationId),
            this.getSectionDataByJobId('lessons_learned', jobApplicationId),
            this.getSectionDataByJobId('performance_metrics', jobApplicationId),
            this.getSectionDataByJobId('advisor_review', jobApplicationId)
        ]);
        // Get skill assessments for each skills matrix
        const skillAssessments = [];
        for (const matrix of skillsMatrix) {
            const assessments = await this.getSectionDataByJobId('skill_assessments', matrix.id);
            skillAssessments.push(...assessments);
        }
        return {
            jobApplication,
            positionDetails,
            jobRequirements,
            companyInformation,
            skillsMatrix,
            skillAssessments,
            applicationMaterials,
            interviewSchedule,
            interviewPreparation,
            communicationLog,
            keyContacts,
            interviewFeedback,
            offerDetails,
            rejectionAnalysis,
            privacyPolicy,
            lessonsLearned,
            performanceMetrics,
            advisorReview
        };
    }
    // Delete job application and all related data
    async deleteJobApplication(jobApplicationId) {
        return new Promise((resolve, reject) => {
            if (!this.db) {
                reject(new Error('Database not initialized'));
                return;
            }
            const tables = [
                'job_applications',
                'position_details',
                'job_requirements',
                'company_information',
                'skills_matrix',
                'skill_assessments',
                'application_materials',
                'interview_schedule',
                'interview_preparation',
                'communication_log',
                'key_contacts',
                'interview_feedback',
                'offer_details',
                'rejection_analysis',
                'privacy_policy',
                'lessons_learned',
                'performance_metrics',
                'advisor_review'
            ];
            const transaction = this.db.transaction(tables, 'readwrite');
            // Delete from job_applications table
            const jobApplicationsStore = transaction.objectStore('job_applications');
            const jobApplicationRequest = jobApplicationsStore.delete(jobApplicationId);
            // Delete from all other tables
            const deletePromises = tables.slice(1).map(tableName => {
                return new Promise((resolveDelete, rejectDelete) => {
                    const store = transaction.objectStore(tableName);
                    const index = store.index('job_application_id');
                    const request = index.getAllKeys(jobApplicationId);
                    request.onsuccess = () => {
                        const keys = request.result;
                        if (keys && keys.length > 0) {
                            keys.forEach(key => {
                                store.delete(key);
                            });
                        }
                        resolveDelete();
                    };
                    request.onerror = () => rejectDelete(request.error);
                });
            });
            transaction.oncomplete = () => resolve();
            transaction.onerror = () => reject(transaction.error);
            Promise.all(deletePromises).catch(reject);
        });
    }
    // Utility method to generate unique IDs
    generateId() {
        return `job_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }
    // Get canonical URL from any URL
    getCanonicalUrl(url) {
        try {
            const urlObj = new URL(url);
            // Remove query parameters and fragments for canonical URL
            return `${urlObj.protocol}//${urlObj.host}${urlObj.pathname}`;
        }
        catch {
            return url;
        }
    }
    // Export database for backup
    async exportDatabase() {
        const jobApplications = await this.getAllJobApplications();
        const exportData = {};
        for (const jobApp of jobApplications) {
            exportData[jobApp.id] = await this.getCompleteJobApplication(jobApp.id);
        }
        return exportData;
    }
    // Import database from backup
    async importDatabase(data) {
        // Clear existing data first
        await this.clearDatabase();
        // Import new data
        for (const originalJobAppId in data) {
            const jobData = data[originalJobAppId];
            // Create job application
            const newJobAppId = await this.createJobApplication({
                canonical_url: jobData.jobApplication.canonical_url,
                job_title: jobData.jobApplication.job_title,
                company_name: jobData.jobApplication.company_name,
                application_date: jobData.jobApplication.application_date,
                status: jobData.jobApplication.status
            });
            // Import all sections
            await Promise.all([
                ...jobData.positionDetails.map((pd) => this.saveSectionData('position_details', { ...pd, job_application_id: newJobAppId })),
                ...jobData.jobRequirements.map((jr) => this.saveSectionData('job_requirements', { ...jr, job_application_id: newJobAppId })),
                // Continue for all other sections...
            ]);
        }
    }
    // Clear all data
    async clearDatabase() {
        return new Promise((resolve, reject) => {
            if (!this.db) {
                reject(new Error('Database not initialized'));
                return;
            }
            const tables = [
                'job_applications',
                'position_details',
                'job_requirements',
                'company_information',
                'skills_matrix',
                'skill_assessments',
                'application_materials',
                'interview_schedule',
                'interview_preparation',
                'communication_log',
                'key_contacts',
                'interview_feedback',
                'offer_details',
                'rejection_analysis',
                'privacy_policy',
                'lessons_learned',
                'performance_metrics',
                'advisor_review'
            ];
            const transaction = this.db.transaction(tables, 'readwrite');
            tables.forEach(tableName => {
                const store = transaction.objectStore(tableName);
                store.clear();
            });
            transaction.oncomplete = () => resolve();
            transaction.onerror = () => reject(transaction.error);
        });
    }
}
// Export singleton instance
export const jobOpsDatabase = new JobOpsDatabase();
//# sourceMappingURL=database.js.map