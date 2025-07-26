// Database schema and operations for JobOps Clipper
// Uses SQLite for local storage with proper table relationships
export class JobOpsDatabase {
    constructor() {
        this.db = null;
        this.dbName = 'JobOpsDatabase';
        this.dbVersion = 1;
        this.initializeDatabase();
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
                this.createTables(db);
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
        }
        // Position details table
        if (!db.objectStoreNames.contains('position_details')) {
            const positionDetailsStore = db.createObjectStore('position_details', { keyPath: 'id' });
            positionDetailsStore.createIndex('job_application_id', 'job_application_id', { unique: false });
        }
        // Job requirements table
        if (!db.objectStoreNames.contains('job_requirements')) {
            const jobRequirementsStore = db.createObjectStore('job_requirements', { keyPath: 'id' });
            jobRequirementsStore.createIndex('job_application_id', 'job_application_id', { unique: false });
        }
        // Company information table
        if (!db.objectStoreNames.contains('company_information')) {
            const companyInformationStore = db.createObjectStore('company_information', { keyPath: 'id' });
            companyInformationStore.createIndex('job_application_id', 'job_application_id', { unique: false });
        }
        // Skills matrix table
        if (!db.objectStoreNames.contains('skills_matrix')) {
            const skillsMatrixStore = db.createObjectStore('skills_matrix', { keyPath: 'id' });
            skillsMatrixStore.createIndex('job_application_id', 'job_application_id', { unique: false });
        }
        // Skill assessments table
        if (!db.objectStoreNames.contains('skill_assessments')) {
            const skillAssessmentsStore = db.createObjectStore('skill_assessments', { keyPath: 'id' });
            skillAssessmentsStore.createIndex('skills_matrix_id', 'skills_matrix_id', { unique: false });
        }
        // Application materials table
        if (!db.objectStoreNames.contains('application_materials')) {
            const applicationMaterialsStore = db.createObjectStore('application_materials', { keyPath: 'id' });
            applicationMaterialsStore.createIndex('job_application_id', 'job_application_id', { unique: false });
        }
        // Interview schedule table
        if (!db.objectStoreNames.contains('interview_schedule')) {
            const interviewScheduleStore = db.createObjectStore('interview_schedule', { keyPath: 'id' });
            interviewScheduleStore.createIndex('job_application_id', 'job_application_id', { unique: false });
        }
        // Interview preparation table
        if (!db.objectStoreNames.contains('interview_preparation')) {
            const interviewPreparationStore = db.createObjectStore('interview_preparation', { keyPath: 'id' });
            interviewPreparationStore.createIndex('job_application_id', 'job_application_id', { unique: false });
        }
        // Communication log table
        if (!db.objectStoreNames.contains('communication_log')) {
            const communicationLogStore = db.createObjectStore('communication_log', { keyPath: 'id' });
            communicationLogStore.createIndex('job_application_id', 'job_application_id', { unique: false });
        }
        // Key contacts table
        if (!db.objectStoreNames.contains('key_contacts')) {
            const keyContactsStore = db.createObjectStore('key_contacts', { keyPath: 'id' });
            keyContactsStore.createIndex('job_application_id', 'job_application_id', { unique: false });
        }
        // Interview feedback table
        if (!db.objectStoreNames.contains('interview_feedback')) {
            const interviewFeedbackStore = db.createObjectStore('interview_feedback', { keyPath: 'id' });
            interviewFeedbackStore.createIndex('job_application_id', 'job_application_id', { unique: false });
        }
        // Offer details table
        if (!db.objectStoreNames.contains('offer_details')) {
            const offerDetailsStore = db.createObjectStore('offer_details', { keyPath: 'id' });
            offerDetailsStore.createIndex('job_application_id', 'job_application_id', { unique: false });
        }
        // Rejection analysis table
        if (!db.objectStoreNames.contains('rejection_analysis')) {
            const rejectionAnalysisStore = db.createObjectStore('rejection_analysis', { keyPath: 'id' });
            rejectionAnalysisStore.createIndex('job_application_id', 'job_application_id', { unique: false });
        }
        // Privacy policy table
        if (!db.objectStoreNames.contains('privacy_policy')) {
            const privacyPolicyStore = db.createObjectStore('privacy_policy', { keyPath: 'id' });
            privacyPolicyStore.createIndex('job_application_id', 'job_application_id', { unique: false });
        }
        // Lessons learned table
        if (!db.objectStoreNames.contains('lessons_learned')) {
            const lessonsLearnedStore = db.createObjectStore('lessons_learned', { keyPath: 'id' });
            lessonsLearnedStore.createIndex('job_application_id', 'job_application_id', { unique: false });
        }
        // Performance metrics table
        if (!db.objectStoreNames.contains('performance_metrics')) {
            const performanceMetricsStore = db.createObjectStore('performance_metrics', { keyPath: 'id' });
            performanceMetricsStore.createIndex('job_application_id', 'job_application_id', { unique: false });
        }
        // Advisor review table
        if (!db.objectStoreNames.contains('advisor_review')) {
            const advisorReviewStore = db.createObjectStore('advisor_review', { keyPath: 'id' });
            advisorReviewStore.createIndex('job_application_id', 'job_application_id', { unique: false });
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
            request.onsuccess = () => {
                resolve(request.result || null);
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
            const request = store.add(record);
            request.onsuccess = () => {
                resolve(id);
            };
            request.onerror = () => {
                reject(request.error);
            };
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
            request.onsuccess = () => {
                resolve(request.result || null);
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
                const updated = {
                    ...existing,
                    ...data,
                    updated_at: new Date().toISOString()
                };
                const putRequest = store.put(updated);
                putRequest.onsuccess = () => resolve();
                putRequest.onerror = () => reject(putRequest.error);
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
            request.onsuccess = () => {
                resolve(request.result || []);
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
            const request = store.add(record);
            request.onsuccess = () => {
                resolve(id);
            };
            request.onerror = () => {
                reject(request.error);
            };
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
            request.onsuccess = () => {
                resolve(request.result || []);
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
                const updated = {
                    ...existing,
                    ...data,
                    updated_at: new Date().toISOString()
                };
                const putRequest = store.put(updated);
                putRequest.onsuccess = () => resolve();
                putRequest.onerror = () => reject(putRequest.error);
            };
            getRequest.onerror = () => reject(getRequest.error);
        });
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
