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
  private readonly dbVersion = 1;

  constructor() {
    this.initializeDatabase();
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
        this.createTables(db);
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

      request.onsuccess = () => {
        resolve(request.result || null);
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
      const record: JobApplicationRecord = {
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
  async getJobApplication(id: string): Promise<JobApplicationRecord | null> {
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

        const updated: JobApplicationRecord = {
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
  async getAllJobApplications(): Promise<JobApplicationRecord[]> {
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

      request.onsuccess = () => {
        resolve(request.result || []);
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
      const assessments = await this.getSectionDataByJobId<SkillAssessmentRecord>('skill_assessments', matrix.id);
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