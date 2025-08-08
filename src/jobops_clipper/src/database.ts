// Database schema and operations for JobOps Clipper
// Uses SQLite for local storage with proper table relationships

export interface DatabaseConfig {
  name: string;
  version: number;
  tables: TableSchema[];
}

export interface TableSchema {
  name: string;
  columns: ColumnSchema[];
  indexes?: IndexSchema[];
}

export interface ColumnSchema {
  name: string;
  type: 'TEXT' | 'INTEGER' | 'REAL' | 'BLOB' | 'BOOLEAN' | 'DATETIME';
  constraints?: string[];
}

export interface IndexSchema {
  name: string;
  columns: string[];
  unique?: boolean;
}

export interface JobApplicationRecord {
  id: string;
  canonical_url: string;
  job_title: string;
  company_name: string;
  application_date: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface PositionDetailsRecord {
  id: string;
  job_application_id: string;
  job_title: string;
  company_name: string;
  application_date: string;
  source_platform: string;
  job_posting_url: string;
  application_deadline: string;
  location: string;
  employment_type: string;
  salary_range: string;
  job_description: string;
  created_at: string;
  updated_at: string;
}

export interface JobRequirementsRecord {
  id: string;
  job_application_id: string;
  required_skills: string;
  preferred_skills: string;
  required_experience: string;
  education_requirements: string;
  technical_requirements: string;
  industry_knowledge: string;
  created_at: string;
  updated_at: string;
}

export interface CompanyInformationRecord {
  id: string;
  job_application_id: string;
  website: string;
  headquarters: string;
  company_size: string;
  annual_revenue: string;
  industry: string;
  company_type: string;
  ceo_leadership: string;
  mission_statement: string;
  core_values: string;
  recent_news: string;
  social_media_presence: string;
  employee_reviews: string;
  main_competitors: string;
  market_position: string;
  unique_selling_points: string;
  created_at: string;
  updated_at: string;
}

export interface SkillsMatrixRecord {
  id: string;
  job_application_id: string;
  identified_gaps: string;
  development_priority: string;
  learning_resources: string;
  improvement_timeline: string;
  created_at: string;
  updated_at: string;
}

export interface SkillAssessmentRecord {
  id: string;
  skills_matrix_id: string;
  skill_category: string;
  required_by_job: boolean;
  current_level: number;
  match_status: string;
  evidence_examples: string;
  created_at: string;
  updated_at: string;
}

export interface ApplicationMaterialsRecord {
  id: string;
  job_application_id: string;
  resume_version: string;
  tailoring_changes: string;
  keywords_added: string;
  sections_modified: string;
  file_name: string;
  cover_letter_version: string;
  key_points_emphasized: string;
  company_specific_content: string;
  call_to_action: string;
  portfolio_items: string;
  references_provided: string;
  additional_documents: string;
  created_at: string;
  updated_at: string;
}

export interface InterviewScheduleRecord {
  id: string;
  job_application_id: string;
  stage: string;
  date: string;
  time: string;
  duration: number;
  format: string;
  interviewers: string;
  location: string;
  platform: string;
  notes: string;
  created_at: string;
  updated_at: string;
}

export interface InterviewPreparationRecord {
  id: string;
  job_application_id: string;
  company_research_completed: boolean;
  questions_for_interviewer: string;
  star_examples_ready: string;
  technical_skills_reviewed: boolean;
  portfolio_ready: boolean;
  attire_prepared: boolean;
  technology_tested: boolean;
  additional_notes: string;
  created_at: string;
  updated_at: string;
}

export interface CommunicationLogRecord {
  id: string;
  job_application_id: string;
  date: string;
  type: string;
  contact_person: string;
  content_summary: string;
  followup_required: boolean;
  response_received: boolean;
  attachments: string;
  created_at: string;
  updated_at: string;
}

export interface KeyContactsRecord {
  id: string;
  job_application_id: string;
  recruiter_name: string;
  recruiter_contact: string;
  hiring_manager: string;
  hr_contact: string;
  employee_referral: string;
  additional_contacts: string;
  created_at: string;
  updated_at: string;
}

export interface InterviewFeedbackRecord {
  id: string;
  job_application_id: string;
  interview_stage: string;
  date: string;
  duration: number;
  self_assessment: string;
  interviewer_feedback: string;
  personal_reflection: string;
  created_at: string;
  updated_at: string;
}

export interface OfferDetailsRecord {
  id: string;
  job_application_id: string;
  position_title: string;
  salary_offered: string;
  benefits_package: string;
  start_date: string;
  decision_deadline: string;
  negotiation_items: string;
  counteroffers: string;
  final_agreement: string;
  created_at: string;
  updated_at: string;
}

export interface RejectionAnalysisRecord {
  id: string;
  job_application_id: string;
  reason_for_rejection: string;
  feedback_received: string;
  areas_for_improvement: string;
  skills_experience_gaps: string;
  created_at: string;
  updated_at: string;
}

export interface PrivacyPolicyRecord {
  id: string;
  job_application_id: string;
  privacy_policy_reviewed: boolean;
  data_retention_period: string;
  data_usage_consent_given: boolean;
  right_to_data_deletion_understood: boolean;
  personal_data_shared: string;
  background_checks_consented: boolean;
  reference_check_authorization: boolean;
  created_at: string;
  updated_at: string;
}

export interface LessonsLearnedRecord {
  id: string;
  job_application_id: string;
  key_insights: string;
  skills_to_develop: string;
  interview_techniques_to_improve: string;
  resume_adjustments_needed: string;
  resume_improvement_plan: string;
  future_application_strategy: string;
  created_at: string;
  updated_at: string;
}

export interface PerformanceMetricsRecord {
  id: string;
  job_application_id: string;
  application_to_interview_rate: number;
  interview_to_second_round_rate: number;
  final_interview_to_offer_rate: number;
  time_from_application_to_response: number;
  skills_match_percentage: number;
  created_at: string;
  updated_at: string;
}

export interface AdvisorReviewRecord {
  id: string;
  job_application_id: string;
  advisor_name: string;
  review_date: string;
  observations: string;
  action_plan: string;
  created_at: string;
  updated_at: string;
}

export class JobOpsDatabase {
  private db: IDBDatabase | null = null;
  private readonly dbName = 'JobOpsDatabase';
  private readonly dbVersion = 2;
  private readonly allTables: string[] = [
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
  private encryptionEnabled = false;
  private cryptoKey: CryptoKey | null = null;
  private pbkdf2Iterations = 250000;

  constructor() {
    this.initializeDatabase();
  }

  // Public API to configure encryption for the session
  async configureEncryption(enabled: boolean, passphrase?: string): Promise<void> {
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

  isEncryptionEnabled(): boolean {
    return this.encryptionEnabled && !!this.cryptoKey;
  }

  private async getOrCreateSalt(): Promise<Uint8Array> {
    const existing = await this.getMetadata('encryption_salt');
    if (existing && existing.value) {
      return this.base64ToBytes(existing.value as string);
    }
    const salt = crypto.getRandomValues(new Uint8Array(16));
    await this.setMetadata('encryption_salt', this.bytesToBase64(salt));
    return salt;
  }

  private async getMetadata(key: string): Promise<{ key: string; value: unknown; updated_at: string } | null> {
    if (!this.db) throw new Error('Database not initialized');
    return new Promise((resolve, reject) => {
      if (!this.db!.objectStoreNames.contains('metadata')) {
        resolve(null);
        return;
      }
      const tx = this.db!.transaction(['metadata'], 'readonly');
      const store = tx.objectStore('metadata');
      const req = store.get(key);
      req.onsuccess = () => resolve(req.result || null);
      req.onerror = () => reject(req.error);
    });
  }

  private async setMetadata(key: string, value: unknown): Promise<void> {
    if (!this.db) throw new Error('Database not initialized');
    return new Promise((resolve, reject) => {
      if (!this.db!.objectStoreNames.contains('metadata')) {
        // create store is only allowed in onupgradeneeded; ignore here
        resolve();
        return;
      }
      const tx = this.db!.transaction(['metadata'], 'readwrite');
      const store = tx.objectStore('metadata');
      const now = new Date().toISOString();
      const req = store.put({ key, value, updated_at: now });
      req.onsuccess = () => resolve();
      req.onerror = () => reject(req.error);
    });
  }

  private async deriveKey(passphrase: string, salt: Uint8Array): Promise<CryptoKey> {
    const enc = new TextEncoder();
    const baseKey = await crypto.subtle.importKey('raw', enc.encode(passphrase), 'PBKDF2', false, ['deriveKey']);
    return crypto.subtle.deriveKey(
      { name: 'PBKDF2', salt, iterations: this.pbkdf2Iterations, hash: 'SHA-256' },
      baseKey,
      { name: 'AES-GCM', length: 256 },
      false,
      ['encrypt', 'decrypt']
    );
  }

  private async encryptPayload(obj: any): Promise<{ iv: string; data: string; alg: string; v: number }> {
    if (!this.cryptoKey) throw new Error('Encryption key not configured');
    const ivBytes = crypto.getRandomValues(new Uint8Array(12));
    const enc = new TextEncoder();
    const plaintext = enc.encode(JSON.stringify(obj));
    const ciphertext = await crypto.subtle.encrypt({ name: 'AES-GCM', iv: ivBytes }, this.cryptoKey, plaintext);
    return { iv: this.bytesToBase64(ivBytes), data: this.bytesToBase64(new Uint8Array(ciphertext)), alg: 'AES-GCM', v: 1 };
  }

  private async decryptPayload(encBlob: { iv: string; data: string }): Promise<any> {
    if (!this.cryptoKey) throw new Error('Encryption key not configured');
    const iv = this.base64ToBytes(encBlob.iv);
    const data = this.base64ToBytes(encBlob.data);
    const plaintext = await crypto.subtle.decrypt({ name: 'AES-GCM', iv }, this.cryptoKey, data);
    const dec = new TextDecoder();
    return JSON.parse(dec.decode(new Uint8Array(plaintext)));
  }

  private bytesToBase64(bytes: Uint8Array): string {
    let binary = '';
    for (let i = 0; i < bytes.byteLength; i++) binary += String.fromCharCode(bytes[i]);
    return btoa(binary);
  }

  private base64ToBytes(b64: string): Uint8Array {
    const binary = atob(b64);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
    return bytes;
  }

  // Split record into index fields (plaintext) and payload (to encrypt)
  private splitForEncryption(tableName: string, record: any): { indexPart: any; payload: any } {
    const indexFields = new Set<string>(['id', 'created_at', 'updated_at']);
    if ('job_application_id' in record) indexFields.add('job_application_id');
    if (tableName === 'skill_assessments' && 'skills_matrix_id' in record) indexFields.add('skills_matrix_id');
    if (tableName === 'job_applications') {
      if ('canonical_url' in record) indexFields.add('canonical_url');
      if ('status' in record) indexFields.add('status');
    }
    const indexPart: any = {};
    const payload: any = {};
    for (const [k, v] of Object.entries(record)) {
      if (indexFields.has(k)) indexPart[k] = v; else payload[k] = v;
    }
    return { indexPart, payload };
  }

  private async prepareRecordForStore(tableName: string, record: any): Promise<any> {
    if (!this.isEncryptionEnabled()) return record;
    const { indexPart, payload } = this.splitForEncryption(tableName, record);
    const enc = await this.encryptPayload(payload);
    return { ...indexPart, __encrypted: true, __enc: enc };
  }

  private async reconstructRecordFromStore(tableName: string, stored: any): Promise<any> {
    if (!stored || !stored.__encrypted) return stored;
    if (!this.isEncryptionEnabled()) {
      throw new Error('Encryption is enabled for data but no key configured. Please set passphrase in settings.');
    }
    const decrypted = await this.decryptPayload(stored.__enc);
    const { __encrypted, __enc, ...indexPart } = stored;
    return { ...indexPart, ...decrypted };
  }

  private async initializeDatabase(): Promise<void> {
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
        const db = (event.target as IDBOpenDBRequest).result;
        const oldVersion = (event as any).oldVersion || 0;
        this.createTables(db);
        // Migrations for v2
        if (oldVersion < 2) {
          // Metadata store for schema tracking
          if (!db.objectStoreNames.contains('metadata')) {
            const meta = db.createObjectStore('metadata', { keyPath: 'key' });
            try { meta.put({ key: 'schemaVersion', value: 2, updated_at: new Date().toISOString() }); } catch {}
          }
          // Add updated_at indexes to improve diagnostics/queries
          const addUpdatedAtIndex = (storeName: string) => {
            if (db.objectStoreNames.contains(storeName)) {
              const store = (event.currentTarget as IDBOpenDBRequest).transaction?.objectStore(storeName) || (db as any).transaction([storeName], 'versionchange').objectStore(storeName);
              try { store.createIndex('updated_at', 'updated_at', { unique: false }); } catch {}
            }
          };
          this.allTables.forEach(addUpdatedAtIndex);
        }
      };
    });
  }

  private createTables(db: IDBDatabase): void {
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
  async checkJobApplicationExists(canonicalUrl: string): Promise<JobApplicationRecord | null> {
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
        if (!stored) { resolve(null); return; }
        try {
          const rec = await this.reconstructRecordFromStore('job_applications', stored);
          resolve(rec || null);
        } catch (e) {
          reject(e);
        }
      };

      request.onerror = () => {
        reject(request.error);
      };
    });
  }

  // Create new job application
  async createJobApplication(data: Omit<JobApplicationRecord, 'id' | 'created_at' | 'updated_at'>): Promise<string> {
    return new Promise((resolve, reject) => {
      if (!this.db) {
        reject(new Error('Database not initialized'));
        return;
      }

      const id = this.generateId();
      const now = new Date().toISOString();
      const record: any = {
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
        } catch (e) {
          reject(e);
        }
      })();
    });
  }

  // Get job application by ID
  async getJobApplication(id: string): Promise<JobApplicationRecord | null> {
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
        if (!stored) { resolve(null); return; }
        try {
          const rec = await this.reconstructRecordFromStore('job_applications', stored);
          resolve(rec || null);
        } catch (e) {
          reject(e);
        }
      };

      request.onerror = () => {
        reject(request.error);
      };
    });
  }

  // Update job application
  async updateJobApplication(id: string, data: Partial<JobApplicationRecord>): Promise<void> {
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
            const updated: any = {
              ...fullExisting,
              ...data,
              updated_at: new Date().toISOString()
            };
            const prepared = await this.prepareRecordForStore('job_applications', updated);
            const putRequest = store.put(prepared);
            putRequest.onsuccess = () => resolve();
            putRequest.onerror = () => reject(putRequest.error);
          } catch (e) {
            reject(e);
          }
        })();
      };

      getRequest.onerror = () => reject(getRequest.error);
    });
  }

  // Get all job applications
  async getAllJobApplications(): Promise<JobApplicationRecord[]> {
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
          const decrypted = await Promise.all(list.map((r: any) => this.reconstructRecordFromStore('job_applications', r)));
          resolve(decrypted as any);
        } catch (e) {
          reject(e);
        }
      };

      request.onerror = () => {
        reject(request.error);
      };
    });
  }

  // Generic method to save section data
  async saveSectionData<T extends { id?: string; job_application_id: string; created_at?: string; updated_at?: string }>(
    tableName: string,
    data: Omit<T, 'id' | 'created_at' | 'updated_at'>
  ): Promise<string> {
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
      } as any;

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
        } catch (e) {
          reject(e);
        }
      })();
    });
  }

  // Generic method to get section data by job application ID
  async getSectionDataByJobId<T>(tableName: string, jobApplicationId: string): Promise<T[]> {
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
          const decrypted = await Promise.all(list.map((r: any) => this.reconstructRecordFromStore(tableName, r)));
          resolve(decrypted as any);
        } catch (e) {
          reject(e);
        }
      };

      request.onerror = () => {
        reject(request.error);
      };
    });
  }

  // Generic method to update section data
  async updateSectionData<T extends { id: string; updated_at?: string }>(
    tableName: string,
    id: string,
    data: Partial<T>
  ): Promise<void> {
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
            } as any;
            const prepared = await this.prepareRecordForStore(tableName, updated);
            const putRequest = store.put(prepared);
            putRequest.onsuccess = () => resolve();
            putRequest.onerror = () => reject(putRequest.error);
          } catch (e) {
            reject(e);
          }
        })();
      };

      getRequest.onerror = () => reject(getRequest.error);
    });
  }

  // Per-table export
  async exportTable(tableName: string): Promise<any[]> {
    if (!this.db) throw new Error('Database not initialized');
    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([tableName], 'readonly');
      const store = transaction.objectStore(tableName);
      const request = store.getAll();
      request.onsuccess = async () => {
        try {
          const list = request.result || [];
          const decrypted = await Promise.all(list.map((r: any) => this.reconstructRecordFromStore(tableName, r)));
          resolve(decrypted);
        } catch (e) {
          reject(e);
        }
      };
      request.onerror = () => reject(request.error);
    });
  }

  // Per-table import (append)
  async importTable(tableName: string, records: any[]): Promise<void> {
    if (!this.db) throw new Error('Database not initialized');
    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([tableName], 'readwrite');
      const store = transaction.objectStore(tableName);
      (async () => {
        try {
          for (const rec of records) {
            const prepared = await this.prepareRecordForStore(tableName, rec);
            store.put(prepared);
          }
          transaction.oncomplete = () => resolve();
          transaction.onerror = () => reject(transaction.error);
        } catch (e) {
          reject(e);
        }
      })();
    });
  }

  // Space usage diagnostics (approximate)
  async getSpaceUsage(): Promise<{ table: string; count: number; approxBytes: number }[]> {
    if (!this.db) throw new Error('Database not initialized');
    const results: { table: string; count: number; approxBytes: number }[] = [];
    for (const table of this.allTables) {
      const rows = await this.exportTable(table);
      const approxBytes = new TextEncoder().encode(JSON.stringify(rows)).length;
      results.push({ table, count: rows.length, approxBytes });
    }
    return results;
  }

  // Get complete job application with all sections
  async getCompleteJobApplication(jobApplicationId: string): Promise<{
    jobApplication: JobApplicationRecord;
    positionDetails: PositionDetailsRecord[];
    jobRequirements: JobRequirementsRecord[];
    companyInformation: CompanyInformationRecord[];
    skillsMatrix: SkillsMatrixRecord[];
    skillAssessments: SkillAssessmentRecord[];
    applicationMaterials: ApplicationMaterialsRecord[];
    interviewSchedule: InterviewScheduleRecord[];
    interviewPreparation: InterviewPreparationRecord[];
    communicationLog: CommunicationLogRecord[];
    keyContacts: KeyContactsRecord[];
    interviewFeedback: InterviewFeedbackRecord[];
    offerDetails: OfferDetailsRecord[];
    rejectionAnalysis: RejectionAnalysisRecord[];
    privacyPolicy: PrivacyPolicyRecord[];
    lessonsLearned: LessonsLearnedRecord[];
    performanceMetrics: PerformanceMetricsRecord[];
    advisorReview: AdvisorReviewRecord[];
  }> {
    const jobApplication = await this.getJobApplication(jobApplicationId);
    if (!jobApplication) {
      throw new Error('Job application not found');
    }

    const [
      positionDetails,
      jobRequirements,
      companyInformation,
      skillsMatrix,
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
    ] = await Promise.all([
      this.getSectionDataByJobId<PositionDetailsRecord>('position_details', jobApplicationId),
      this.getSectionDataByJobId<JobRequirementsRecord>('job_requirements', jobApplicationId),
      this.getSectionDataByJobId<CompanyInformationRecord>('company_information', jobApplicationId),
      this.getSectionDataByJobId<SkillsMatrixRecord>('skills_matrix', jobApplicationId),
      this.getSectionDataByJobId<ApplicationMaterialsRecord>('application_materials', jobApplicationId),
      this.getSectionDataByJobId<InterviewScheduleRecord>('interview_schedule', jobApplicationId),
      this.getSectionDataByJobId<InterviewPreparationRecord>('interview_preparation', jobApplicationId),
      this.getSectionDataByJobId<CommunicationLogRecord>('communication_log', jobApplicationId),
      this.getSectionDataByJobId<KeyContactsRecord>('key_contacts', jobApplicationId),
      this.getSectionDataByJobId<InterviewFeedbackRecord>('interview_feedback', jobApplicationId),
      this.getSectionDataByJobId<OfferDetailsRecord>('offer_details', jobApplicationId),
      this.getSectionDataByJobId<RejectionAnalysisRecord>('rejection_analysis', jobApplicationId),
      this.getSectionDataByJobId<PrivacyPolicyRecord>('privacy_policy', jobApplicationId),
      this.getSectionDataByJobId<LessonsLearnedRecord>('lessons_learned', jobApplicationId),
      this.getSectionDataByJobId<PerformanceMetricsRecord>('performance_metrics', jobApplicationId),
      this.getSectionDataByJobId<AdvisorReviewRecord>('advisor_review', jobApplicationId)
    ]);

    // Get skill assessments for each skills matrix
    const skillAssessments: SkillAssessmentRecord[] = [];
    for (const matrix of skillsMatrix) {
      const assessments = await this.getSectionDataByJobId<SkillAssessmentRecord>('skill_assessments', (matrix as any).id);
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
  async deleteJobApplication(jobApplicationId: string): Promise<void> {
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
        return new Promise<void>((resolveDelete, rejectDelete) => {
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
  private generateId(): string {
    return `job_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  // Get canonical URL from any URL
  getCanonicalUrl(url: string): string {
    try {
      const urlObj = new URL(url);
      // Remove query parameters and fragments for canonical URL
      return `${urlObj.protocol}//${urlObj.host}${urlObj.pathname}`;
    } catch {
      return url;
    }
  }

  // Export database for backup
  async exportDatabase(): Promise<any> {
    const jobApplications = await this.getAllJobApplications();
    const exportData: any = {};

    for (const jobApp of jobApplications) {
      exportData[jobApp.id] = await this.getCompleteJobApplication(jobApp.id);
    }

    return exportData;
  }

  // Import database from backup
  async importDatabase(data: any): Promise<void> {
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
        ...jobData.positionDetails.map((pd: any) => 
          this.saveSectionData('position_details', { ...pd, job_application_id: newJobAppId })
        ),
        ...jobData.jobRequirements.map((jr: any) => 
          this.saveSectionData('job_requirements', { ...jr, job_application_id: newJobAppId })
        ),
        // Continue for all other sections...
      ]);
    }
  }

  // Clear all data
  async clearDatabase(): Promise<void> {
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