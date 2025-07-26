"use strict";
(() => {
  // src/database.ts
  var JobOpsDatabase = class {
    constructor() {
      this.db = null;
      this.dbName = "JobOpsDatabase";
      this.dbVersion = 1;
      this.initializeDatabase();
    }
    async initializeDatabase() {
      return new Promise((resolve, reject) => {
        const request = indexedDB.open(this.dbName, this.dbVersion);
        request.onerror = () => {
          console.error("Failed to open database:", request.error);
          reject(request.error);
        };
        request.onsuccess = () => {
          this.db = request.result;
          console.log("Database opened successfully");
          resolve();
        };
        request.onupgradeneeded = (event) => {
          const db = event.target.result;
          this.createTables(db);
        };
      });
    }
    createTables(db) {
      if (!db.objectStoreNames.contains("job_applications")) {
        const jobApplicationsStore = db.createObjectStore("job_applications", { keyPath: "id" });
        jobApplicationsStore.createIndex("canonical_url", "canonical_url", { unique: true });
        jobApplicationsStore.createIndex("status", "status", { unique: false });
        jobApplicationsStore.createIndex("created_at", "created_at", { unique: false });
      }
      if (!db.objectStoreNames.contains("position_details")) {
        const positionDetailsStore = db.createObjectStore("position_details", { keyPath: "id" });
        positionDetailsStore.createIndex("job_application_id", "job_application_id", { unique: false });
      }
      if (!db.objectStoreNames.contains("job_requirements")) {
        const jobRequirementsStore = db.createObjectStore("job_requirements", { keyPath: "id" });
        jobRequirementsStore.createIndex("job_application_id", "job_application_id", { unique: false });
      }
      if (!db.objectStoreNames.contains("company_information")) {
        const companyInformationStore = db.createObjectStore("company_information", { keyPath: "id" });
        companyInformationStore.createIndex("job_application_id", "job_application_id", { unique: false });
      }
      if (!db.objectStoreNames.contains("skills_matrix")) {
        const skillsMatrixStore = db.createObjectStore("skills_matrix", { keyPath: "id" });
        skillsMatrixStore.createIndex("job_application_id", "job_application_id", { unique: false });
      }
      if (!db.objectStoreNames.contains("skill_assessments")) {
        const skillAssessmentsStore = db.createObjectStore("skill_assessments", { keyPath: "id" });
        skillAssessmentsStore.createIndex("skills_matrix_id", "skills_matrix_id", { unique: false });
      }
      if (!db.objectStoreNames.contains("application_materials")) {
        const applicationMaterialsStore = db.createObjectStore("application_materials", { keyPath: "id" });
        applicationMaterialsStore.createIndex("job_application_id", "job_application_id", { unique: false });
      }
      if (!db.objectStoreNames.contains("interview_schedule")) {
        const interviewScheduleStore = db.createObjectStore("interview_schedule", { keyPath: "id" });
        interviewScheduleStore.createIndex("job_application_id", "job_application_id", { unique: false });
      }
      if (!db.objectStoreNames.contains("interview_preparation")) {
        const interviewPreparationStore = db.createObjectStore("interview_preparation", { keyPath: "id" });
        interviewPreparationStore.createIndex("job_application_id", "job_application_id", { unique: false });
      }
      if (!db.objectStoreNames.contains("communication_log")) {
        const communicationLogStore = db.createObjectStore("communication_log", { keyPath: "id" });
        communicationLogStore.createIndex("job_application_id", "job_application_id", { unique: false });
      }
      if (!db.objectStoreNames.contains("key_contacts")) {
        const keyContactsStore = db.createObjectStore("key_contacts", { keyPath: "id" });
        keyContactsStore.createIndex("job_application_id", "job_application_id", { unique: false });
      }
      if (!db.objectStoreNames.contains("interview_feedback")) {
        const interviewFeedbackStore = db.createObjectStore("interview_feedback", { keyPath: "id" });
        interviewFeedbackStore.createIndex("job_application_id", "job_application_id", { unique: false });
      }
      if (!db.objectStoreNames.contains("offer_details")) {
        const offerDetailsStore = db.createObjectStore("offer_details", { keyPath: "id" });
        offerDetailsStore.createIndex("job_application_id", "job_application_id", { unique: false });
      }
      if (!db.objectStoreNames.contains("rejection_analysis")) {
        const rejectionAnalysisStore = db.createObjectStore("rejection_analysis", { keyPath: "id" });
        rejectionAnalysisStore.createIndex("job_application_id", "job_application_id", { unique: false });
      }
      if (!db.objectStoreNames.contains("privacy_policy")) {
        const privacyPolicyStore = db.createObjectStore("privacy_policy", { keyPath: "id" });
        privacyPolicyStore.createIndex("job_application_id", "job_application_id", { unique: false });
      }
      if (!db.objectStoreNames.contains("lessons_learned")) {
        const lessonsLearnedStore = db.createObjectStore("lessons_learned", { keyPath: "id" });
        lessonsLearnedStore.createIndex("job_application_id", "job_application_id", { unique: false });
      }
      if (!db.objectStoreNames.contains("performance_metrics")) {
        const performanceMetricsStore = db.createObjectStore("performance_metrics", { keyPath: "id" });
        performanceMetricsStore.createIndex("job_application_id", "job_application_id", { unique: false });
      }
      if (!db.objectStoreNames.contains("advisor_review")) {
        const advisorReviewStore = db.createObjectStore("advisor_review", { keyPath: "id" });
        advisorReviewStore.createIndex("job_application_id", "job_application_id", { unique: false });
      }
    }
    // Check if job application exists by canonical URL
    async checkJobApplicationExists(canonicalUrl) {
      return new Promise((resolve, reject) => {
        if (!this.db) {
          reject(new Error("Database not initialized"));
          return;
        }
        const transaction = this.db.transaction(["job_applications"], "readonly");
        const store = transaction.objectStore("job_applications");
        const index = store.index("canonical_url");
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
          reject(new Error("Database not initialized"));
          return;
        }
        const id = this.generateId();
        const now = (/* @__PURE__ */ new Date()).toISOString();
        const record = {
          ...data,
          id,
          created_at: now,
          updated_at: now
        };
        const transaction = this.db.transaction(["job_applications"], "readwrite");
        const store = transaction.objectStore("job_applications");
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
          reject(new Error("Database not initialized"));
          return;
        }
        const transaction = this.db.transaction(["job_applications"], "readonly");
        const store = transaction.objectStore("job_applications");
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
          reject(new Error("Database not initialized"));
          return;
        }
        const transaction = this.db.transaction(["job_applications"], "readwrite");
        const store = transaction.objectStore("job_applications");
        const getRequest = store.get(id);
        getRequest.onsuccess = () => {
          const existing = getRequest.result;
          if (!existing) {
            reject(new Error("Job application not found"));
            return;
          }
          const updated = {
            ...existing,
            ...data,
            updated_at: (/* @__PURE__ */ new Date()).toISOString()
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
          reject(new Error("Database not initialized"));
          return;
        }
        const transaction = this.db.transaction(["job_applications"], "readonly");
        const store = transaction.objectStore("job_applications");
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
          reject(new Error("Database not initialized"));
          return;
        }
        const id = this.generateId();
        const now = (/* @__PURE__ */ new Date()).toISOString();
        const record = {
          ...data,
          id,
          created_at: now,
          updated_at: now
        };
        const transaction = this.db.transaction([tableName], "readwrite");
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
          reject(new Error("Database not initialized"));
          return;
        }
        const transaction = this.db.transaction([tableName], "readonly");
        const store = transaction.objectStore(tableName);
        const index = store.index("job_application_id");
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
          reject(new Error("Database not initialized"));
          return;
        }
        const transaction = this.db.transaction([tableName], "readwrite");
        const store = transaction.objectStore(tableName);
        const getRequest = store.get(id);
        getRequest.onsuccess = () => {
          const existing = getRequest.result;
          if (!existing) {
            reject(new Error("Record not found"));
            return;
          }
          const updated = {
            ...existing,
            ...data,
            updated_at: (/* @__PURE__ */ new Date()).toISOString()
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
        throw new Error("Job application not found");
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
        this.getSectionDataByJobId("position_details", jobApplicationId),
        this.getSectionDataByJobId("job_requirements", jobApplicationId),
        this.getSectionDataByJobId("company_information", jobApplicationId),
        this.getSectionDataByJobId("skills_matrix", jobApplicationId),
        this.getSectionDataByJobId("application_materials", jobApplicationId),
        this.getSectionDataByJobId("interview_schedule", jobApplicationId),
        this.getSectionDataByJobId("interview_preparation", jobApplicationId),
        this.getSectionDataByJobId("communication_log", jobApplicationId),
        this.getSectionDataByJobId("key_contacts", jobApplicationId),
        this.getSectionDataByJobId("interview_feedback", jobApplicationId),
        this.getSectionDataByJobId("offer_details", jobApplicationId),
        this.getSectionDataByJobId("rejection_analysis", jobApplicationId),
        this.getSectionDataByJobId("privacy_policy", jobApplicationId),
        this.getSectionDataByJobId("lessons_learned", jobApplicationId),
        this.getSectionDataByJobId("performance_metrics", jobApplicationId),
        this.getSectionDataByJobId("advisor_review", jobApplicationId)
      ]);
      const skillAssessments = [];
      for (const matrix of skillsMatrix) {
        const assessments = await this.getSectionDataByJobId("skill_assessments", matrix.id);
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
          reject(new Error("Database not initialized"));
          return;
        }
        const tables = [
          "job_applications",
          "position_details",
          "job_requirements",
          "company_information",
          "skills_matrix",
          "skill_assessments",
          "application_materials",
          "interview_schedule",
          "interview_preparation",
          "communication_log",
          "key_contacts",
          "interview_feedback",
          "offer_details",
          "rejection_analysis",
          "privacy_policy",
          "lessons_learned",
          "performance_metrics",
          "advisor_review"
        ];
        const transaction = this.db.transaction(tables, "readwrite");
        const jobApplicationsStore = transaction.objectStore("job_applications");
        const jobApplicationRequest = jobApplicationsStore.delete(jobApplicationId);
        const deletePromises = tables.slice(1).map((tableName) => {
          return new Promise((resolveDelete, rejectDelete) => {
            const store = transaction.objectStore(tableName);
            const index = store.index("job_application_id");
            const request = index.getAllKeys(jobApplicationId);
            request.onsuccess = () => {
              const keys = request.result;
              if (keys && keys.length > 0) {
                keys.forEach((key) => {
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
        return `${urlObj.protocol}//${urlObj.host}${urlObj.pathname}`;
      } catch {
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
      await this.clearDatabase();
      for (const originalJobAppId in data) {
        const jobData = data[originalJobAppId];
        const newJobAppId = await this.createJobApplication({
          canonical_url: jobData.jobApplication.canonical_url,
          job_title: jobData.jobApplication.job_title,
          company_name: jobData.jobApplication.company_name,
          application_date: jobData.jobApplication.application_date,
          status: jobData.jobApplication.status
        });
        await Promise.all([
          ...jobData.positionDetails.map(
            (pd) => this.saveSectionData("position_details", { ...pd, job_application_id: newJobAppId })
          ),
          ...jobData.jobRequirements.map(
            (jr) => this.saveSectionData("job_requirements", { ...jr, job_application_id: newJobAppId })
          )
          // Continue for all other sections...
        ]);
      }
    }
    // Clear all data
    async clearDatabase() {
      return new Promise((resolve, reject) => {
        if (!this.db) {
          reject(new Error("Database not initialized"));
          return;
        }
        const tables = [
          "job_applications",
          "position_details",
          "job_requirements",
          "company_information",
          "skills_matrix",
          "skill_assessments",
          "application_materials",
          "interview_schedule",
          "interview_preparation",
          "communication_log",
          "key_contacts",
          "interview_feedback",
          "offer_details",
          "rejection_analysis",
          "privacy_policy",
          "lessons_learned",
          "performance_metrics",
          "advisor_review"
        ];
        const transaction = this.db.transaction(tables, "readwrite");
        tables.forEach((tableName) => {
          const store = transaction.objectStore(tableName);
          store.clear();
        });
        transaction.oncomplete = () => resolve();
        transaction.onerror = () => reject(transaction.error);
      });
    }
  };
  var jobOpsDatabase = new JobOpsDatabase();

  // src/repository.ts
  var JobOpsDataManager = class {
    constructor() {
      this.currentJobApplicationId = null;
      this.currentCanonicalUrl = null;
      this.initializeDataManager();
    }
    async initializeDataManager() {
      try {
        await new Promise((resolve) => setTimeout(resolve, 100));
        console.log("JobOps Data Manager initialized");
      } catch (error) {
        console.error("Failed to initialize data manager:", error);
      }
    }
    // Check if job application exists and load it if it does
    async checkAndLoadExistingJob(url) {
      try {
        const canonicalUrl = jobOpsDatabase.getCanonicalUrl(url);
        this.currentCanonicalUrl = canonicalUrl;
        const existingJob = await jobOpsDatabase.checkJobApplicationExists(canonicalUrl);
        if (existingJob) {
          this.currentJobApplicationId = existingJob.id;
          await this.loadJobApplicationData(existingJob.id);
          return true;
        }
        return false;
      } catch (error) {
        console.error("Error checking existing job:", error);
        return false;
      }
    }
    // Create new job application
    async createNewJobApplication(jobData) {
      try {
        const canonicalUrl = jobOpsDatabase.getCanonicalUrl(jobData.url || "");
        this.currentCanonicalUrl = canonicalUrl;
        const jobApplicationData = {
          canonical_url: canonicalUrl,
          job_title: jobData.title || "",
          company_name: jobData.company || "",
          application_date: (/* @__PURE__ */ new Date()).toISOString(),
          status: "draft"
        };
        this.currentJobApplicationId = await jobOpsDatabase.createJobApplication(jobApplicationData);
        console.log("New job application created:", this.currentJobApplicationId);
        return this.currentJobApplicationId;
      } catch (error) {
        console.error("Error creating new job application:", error);
        throw error;
      }
    }
    // Load all data for a job application
    async loadJobApplicationData(jobApplicationId) {
      try {
        const completeData = await jobOpsDatabase.getCompleteJobApplication(jobApplicationId);
        this.populateUIWithData(completeData);
      } catch (error) {
        console.error("Error loading job application data:", error);
      }
    }
    // Save position details
    async savePositionDetails(data) {
      if (!this.currentJobApplicationId) {
        throw new Error("No active job application");
      }
      try {
        const positionDetailsData = {
          job_application_id: this.currentJobApplicationId,
          job_title: data.jobTitle || "",
          company_name: data.companyName || "",
          application_date: data.applicationDate || (/* @__PURE__ */ new Date()).toISOString(),
          source_platform: data.sourcePlatform || "",
          job_posting_url: data.jobPostingUrl || "",
          application_deadline: data.applicationDeadline || "",
          location: data.location || "",
          employment_type: data.employmentType || "",
          salary_range: data.salaryRange || "",
          job_description: data.jobDescription || ""
        };
        await jobOpsDatabase.saveSectionData("position_details", positionDetailsData);
        console.log("Position details saved");
      } catch (error) {
        console.error("Error saving position details:", error);
        throw error;
      }
    }
    // Save job requirements
    async saveJobRequirements(data) {
      if (!this.currentJobApplicationId) {
        throw new Error("No active job application");
      }
      try {
        const jobRequirementsData = {
          job_application_id: this.currentJobApplicationId,
          required_skills: JSON.stringify(data.requiredSkills || []),
          preferred_skills: JSON.stringify(data.preferredSkills || []),
          required_experience: data.requiredExperience || "",
          education_requirements: JSON.stringify(data.educationRequirements || []),
          technical_requirements: JSON.stringify(data.technicalRequirements || []),
          industry_knowledge: JSON.stringify(data.industryKnowledge || [])
        };
        await jobOpsDatabase.saveSectionData("job_requirements", jobRequirementsData);
        console.log("Job requirements saved");
      } catch (error) {
        console.error("Error saving job requirements:", error);
        throw error;
      }
    }
    // Save company information
    async saveCompanyInformation(data) {
      if (!this.currentJobApplicationId) {
        throw new Error("No active job application");
      }
      try {
        const companyInformationData = {
          job_application_id: this.currentJobApplicationId,
          website: data.website || "",
          headquarters: data.headquarters || "",
          company_size: data.companySize || "",
          annual_revenue: data.annualRevenue || "",
          industry: data.industry || "",
          company_type: data.companyType || "",
          ceo_leadership: data.ceoLeadership || "",
          mission_statement: data.missionStatement || "",
          core_values: JSON.stringify(data.coreValues || []),
          recent_news: JSON.stringify(data.recentNews || []),
          social_media_presence: JSON.stringify(data.socialMediaPresence || {}),
          employee_reviews: data.employeeReviews || "",
          main_competitors: JSON.stringify(data.mainCompetitors || []),
          market_position: data.marketPosition || "",
          unique_selling_points: JSON.stringify(data.uniqueSellingPoints || [])
        };
        await jobOpsDatabase.saveSectionData("company_information", companyInformationData);
        console.log("Company information saved");
      } catch (error) {
        console.error("Error saving company information:", error);
        throw error;
      }
    }
    // Save skills matrix
    async saveSkillsMatrix(data) {
      if (!this.currentJobApplicationId) {
        throw new Error("No active job application");
      }
      try {
        const skillsMatrixData = {
          job_application_id: this.currentJobApplicationId,
          identified_gaps: JSON.stringify(data.identifiedGaps || []),
          development_priority: data.developmentPriority || "medium",
          learning_resources: JSON.stringify(data.learningResources || []),
          improvement_timeline: data.improvementTimeline || ""
        };
        const skillsMatrixId = await jobOpsDatabase.saveSectionData("skills_matrix", skillsMatrixData);
        if (data.assessments && Array.isArray(data.assessments)) {
          for (const assessment of data.assessments) {
            const skillAssessmentData = {
              skills_matrix_id: skillsMatrixId,
              skill_category: assessment.skillCategory || "",
              required_by_job: assessment.requiredByJob || false,
              current_level: assessment.currentLevel || 1,
              match_status: assessment.matchStatus || "partial_match",
              evidence_examples: JSON.stringify(assessment.evidenceExamples || [])
            };
            await jobOpsDatabase.saveSectionData("skill_assessments", skillAssessmentData);
          }
        }
        console.log("Skills matrix saved");
      } catch (error) {
        console.error("Error saving skills matrix:", error);
        throw error;
      }
    }
    // Save application materials
    async saveApplicationMaterials(data) {
      if (!this.currentJobApplicationId) {
        throw new Error("No active job application");
      }
      try {
        const applicationMaterialsData = {
          job_application_id: this.currentJobApplicationId,
          resume_version: data.resumeVersion || "",
          tailoring_changes: JSON.stringify(data.tailoringChanges || []),
          keywords_added: JSON.stringify(data.keywordsAdded || []),
          sections_modified: JSON.stringify(data.sectionsModified || []),
          file_name: data.fileName || "",
          cover_letter_version: data.coverLetterVersion || "",
          key_points_emphasized: JSON.stringify(data.keyPointsEmphasized || []),
          company_specific_content: JSON.stringify(data.companySpecificContent || []),
          call_to_action: data.callToAction || "",
          portfolio_items: JSON.stringify(data.portfolioItems || []),
          references_provided: JSON.stringify(data.referencesProvided || []),
          additional_documents: JSON.stringify(data.additionalDocuments || [])
        };
        await jobOpsDatabase.saveSectionData("application_materials", applicationMaterialsData);
        console.log("Application materials saved");
      } catch (error) {
        console.error("Error saving application materials:", error);
        throw error;
      }
    }
    // Save interview schedule
    async saveInterviewSchedule(data) {
      if (!this.currentJobApplicationId) {
        throw new Error("No active job application");
      }
      try {
        const interviewScheduleData = {
          job_application_id: this.currentJobApplicationId,
          stage: data.stage || "",
          date: data.date || "",
          time: data.time || "",
          duration: data.duration || 0,
          format: data.format || "",
          interviewers: JSON.stringify(data.interviewers || []),
          location: data.location || "",
          platform: data.platform || "",
          notes: data.notes || ""
        };
        await jobOpsDatabase.saveSectionData("interview_schedule", interviewScheduleData);
        console.log("Interview schedule saved");
      } catch (error) {
        console.error("Error saving interview schedule:", error);
        throw error;
      }
    }
    // Save interview preparation
    async saveInterviewPreparation(data) {
      if (!this.currentJobApplicationId) {
        throw new Error("No active job application");
      }
      try {
        const interviewPreparationData = {
          job_application_id: this.currentJobApplicationId,
          company_research_completed: data.companyResearchCompleted || false,
          questions_for_interviewer: JSON.stringify(data.questionsForInterviewer || []),
          star_examples_ready: JSON.stringify(data.starExamplesReady || []),
          technical_skills_reviewed: data.technicalSkillsReviewed || false,
          portfolio_ready: data.portfolioReady || false,
          attire_prepared: data.attirePrepared || false,
          technology_tested: data.technologyTested || false,
          additional_notes: data.additionalNotes || ""
        };
        await jobOpsDatabase.saveSectionData("interview_preparation", interviewPreparationData);
        console.log("Interview preparation saved");
      } catch (error) {
        console.error("Error saving interview preparation:", error);
        throw error;
      }
    }
    // Save communication log
    async saveCommunicationLog(data) {
      if (!this.currentJobApplicationId) {
        throw new Error("No active job application");
      }
      try {
        const communicationLogData = {
          job_application_id: this.currentJobApplicationId,
          date: data.date || (/* @__PURE__ */ new Date()).toISOString(),
          type: data.type || "",
          contact_person: data.contactPerson || "",
          content_summary: data.contentSummary || "",
          followup_required: data.followupRequired || false,
          response_received: data.responseReceived || false,
          attachments: JSON.stringify(data.attachments || [])
        };
        await jobOpsDatabase.saveSectionData("communication_log", communicationLogData);
        console.log("Communication log saved");
      } catch (error) {
        console.error("Error saving communication log:", error);
        throw error;
      }
    }
    // Save key contacts
    async saveKeyContacts(data) {
      if (!this.currentJobApplicationId) {
        throw new Error("No active job application");
      }
      try {
        const keyContactsData = {
          job_application_id: this.currentJobApplicationId,
          recruiter_name: data.recruiterName || "",
          recruiter_contact: data.recruiterContact || "",
          hiring_manager: data.hiringManager || "",
          hr_contact: data.hrContact || "",
          employee_referral: data.employeeReferral || "",
          additional_contacts: JSON.stringify(data.additionalContacts || {})
        };
        await jobOpsDatabase.saveSectionData("key_contacts", keyContactsData);
        console.log("Key contacts saved");
      } catch (error) {
        console.error("Error saving key contacts:", error);
        throw error;
      }
    }
    // Save interview feedback
    async saveInterviewFeedback(data) {
      if (!this.currentJobApplicationId) {
        throw new Error("No active job application");
      }
      try {
        const interviewFeedbackData = {
          job_application_id: this.currentJobApplicationId,
          interview_stage: data.interviewStage || "",
          date: data.date || (/* @__PURE__ */ new Date()).toISOString(),
          duration: data.duration || 0,
          self_assessment: JSON.stringify(data.selfAssessment || {}),
          interviewer_feedback: JSON.stringify(data.interviewerFeedback || {}),
          personal_reflection: JSON.stringify(data.personalReflection || {})
        };
        await jobOpsDatabase.saveSectionData("interview_feedback", interviewFeedbackData);
        console.log("Interview feedback saved");
      } catch (error) {
        console.error("Error saving interview feedback:", error);
        throw error;
      }
    }
    // Save offer details
    async saveOfferDetails(data) {
      if (!this.currentJobApplicationId) {
        throw new Error("No active job application");
      }
      try {
        const offerDetailsData = {
          job_application_id: this.currentJobApplicationId,
          position_title: data.positionTitle || "",
          salary_offered: data.salaryOffered || "",
          benefits_package: JSON.stringify(data.benefitsPackage || []),
          start_date: data.startDate || "",
          decision_deadline: data.decisionDeadline || "",
          negotiation_items: JSON.stringify(data.negotiationItems || []),
          counteroffers: JSON.stringify(data.counteroffers || []),
          final_agreement: data.finalAgreement || ""
        };
        await jobOpsDatabase.saveSectionData("offer_details", offerDetailsData);
        console.log("Offer details saved");
      } catch (error) {
        console.error("Error saving offer details:", error);
        throw error;
      }
    }
    // Save rejection analysis
    async saveRejectionAnalysis(data) {
      if (!this.currentJobApplicationId) {
        throw new Error("No active job application");
      }
      try {
        const rejectionAnalysisData = {
          job_application_id: this.currentJobApplicationId,
          reason_for_rejection: data.reasonForRejection || "",
          feedback_received: JSON.stringify(data.feedbackReceived || []),
          areas_for_improvement: JSON.stringify(data.areasForImprovement || []),
          skills_experience_gaps: JSON.stringify(data.skillsExperienceGaps || [])
        };
        await jobOpsDatabase.saveSectionData("rejection_analysis", rejectionAnalysisData);
        console.log("Rejection analysis saved");
      } catch (error) {
        console.error("Error saving rejection analysis:", error);
        throw error;
      }
    }
    // Save privacy policy
    async savePrivacyPolicy(data) {
      if (!this.currentJobApplicationId) {
        throw new Error("No active job application");
      }
      try {
        const privacyPolicyData = {
          job_application_id: this.currentJobApplicationId,
          privacy_policy_reviewed: data.privacyPolicyReviewed || false,
          data_retention_period: data.dataRetentionPeriod || "",
          data_usage_consent_given: data.dataUsageConsentGiven || false,
          right_to_data_deletion_understood: data.rightToDataDeletionUnderstood || false,
          personal_data_shared: JSON.stringify(data.personalDataShared || []),
          background_checks_consented: data.backgroundChecksConsented || false,
          reference_check_authorization: data.referenceCheckAuthorization || false
        };
        await jobOpsDatabase.saveSectionData("privacy_policy", privacyPolicyData);
        console.log("Privacy policy saved");
      } catch (error) {
        console.error("Error saving privacy policy:", error);
        throw error;
      }
    }
    // Save lessons learned
    async saveLessonsLearned(data) {
      if (!this.currentJobApplicationId) {
        throw new Error("No active job application");
      }
      try {
        const lessonsLearnedData = {
          job_application_id: this.currentJobApplicationId,
          key_insights: JSON.stringify(data.keyInsights || []),
          skills_to_develop: JSON.stringify(data.skillsToDevelop || []),
          interview_techniques_to_improve: JSON.stringify(data.interviewTechniquesToImprove || []),
          resume_adjustments_needed: JSON.stringify(data.resumeAdjustmentsNeeded || []),
          resume_improvement_plan: JSON.stringify(data.resumeImprovementPlan || {}),
          future_application_strategy: JSON.stringify(data.futureApplicationStrategy || {})
        };
        await jobOpsDatabase.saveSectionData("lessons_learned", lessonsLearnedData);
        console.log("Lessons learned saved");
      } catch (error) {
        console.error("Error saving lessons learned:", error);
        throw error;
      }
    }
    // Save performance metrics
    async savePerformanceMetrics(data) {
      if (!this.currentJobApplicationId) {
        throw new Error("No active job application");
      }
      try {
        const performanceMetricsData = {
          job_application_id: this.currentJobApplicationId,
          application_to_interview_rate: data.applicationToInterviewRate || 0,
          interview_to_second_round_rate: data.interviewToSecondRoundRate || 0,
          final_interview_to_offer_rate: data.finalInterviewToOfferRate || 0,
          time_from_application_to_response: data.timeFromApplicationToResponse || 0,
          skills_match_percentage: data.skillsMatchPercentage || 0
        };
        await jobOpsDatabase.saveSectionData("performance_metrics", performanceMetricsData);
        console.log("Performance metrics saved");
      } catch (error) {
        console.error("Error saving performance metrics:", error);
        throw error;
      }
    }
    // Save advisor review
    async saveAdvisorReview(data) {
      if (!this.currentJobApplicationId) {
        throw new Error("No active job application");
      }
      try {
        const advisorReviewData = {
          job_application_id: this.currentJobApplicationId,
          advisor_name: data.advisorName || "",
          review_date: data.reviewDate || (/* @__PURE__ */ new Date()).toISOString(),
          observations: JSON.stringify(data.observations || {}),
          action_plan: JSON.stringify(data.actionPlan || {})
        };
        await jobOpsDatabase.saveSectionData("advisor_review", advisorReviewData);
        console.log("Advisor review saved");
      } catch (error) {
        console.error("Error saving advisor review:", error);
        throw error;
      }
    }
    // Update job application status
    async updateJobStatus(status) {
      if (!this.currentJobApplicationId) {
        throw new Error("No active job application");
      }
      try {
        await jobOpsDatabase.updateJobApplication(this.currentJobApplicationId, { status });
        console.log("Job status updated to:", status);
      } catch (error) {
        console.error("Error updating job status:", error);
        throw error;
      }
    }
    // Get current job application ID
    getCurrentJobApplicationId() {
      return this.currentJobApplicationId;
    }
    // Get current canonical URL
    getCurrentCanonicalUrl() {
      return this.currentCanonicalUrl;
    }
    // Populate UI with loaded data
    populateUIWithData(data) {
      console.log("Populating UI with loaded data:", data);
    }
    // Export current job application data
    async exportCurrentJobApplication() {
      if (!this.currentJobApplicationId) {
        throw new Error("No active job application");
      }
      try {
        return await jobOpsDatabase.getCompleteJobApplication(this.currentJobApplicationId);
      } catch (error) {
        console.error("Error exporting job application:", error);
        throw error;
      }
    }
    // Delete current job application
    async deleteCurrentJobApplication() {
      if (!this.currentJobApplicationId) {
        throw new Error("No active job application");
      }
      try {
        await jobOpsDatabase.deleteJobApplication(this.currentJobApplicationId);
        this.currentJobApplicationId = null;
        this.currentCanonicalUrl = null;
        console.log("Job application deleted");
      } catch (error) {
        console.error("Error deleting job application:", error);
        throw error;
      }
    }
    // Get all job applications for dashboard
    async getAllJobApplications() {
      try {
        return await jobOpsDatabase.getAllJobApplications();
      } catch (error) {
        console.error("Error getting all job applications:", error);
        throw error;
      }
    }
    // Export entire database
    async exportDatabase() {
      try {
        return await jobOpsDatabase.exportDatabase();
      } catch (error) {
        console.error("Error exporting database:", error);
        throw error;
      }
    }
    // Import database
    async importDatabase(data) {
      try {
        await jobOpsDatabase.importDatabase(data);
        console.log("Database imported successfully");
      } catch (error) {
        console.error("Error importing database:", error);
        throw error;
      }
    }
  };
  var jobOpsDataManager = new JobOpsDataManager();

  // src/popup.ts
  var GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions";
  var GROQ_MODEL = "qwen2.5-32b-instant";
  var OLLAMA_URL = "http://localhost:11434";
  var OLLAMA_MODEL = "qwen3:1.7b";
  var consoleOutput = null;
  var isGenerating = false;
  var abortController = null;
  function logToConsole(message, level = "info") {
    if (!consoleOutput)
      return;
    const timestamp = (/* @__PURE__ */ new Date()).toLocaleTimeString();
    const line = document.createElement("div");
    line.className = `console-line ${level}`;
    line.innerHTML = `<span style="color: #888;">[${timestamp}]</span> ${message}`;
    consoleOutput.appendChild(line);
    consoleOutput.scrollTop = consoleOutput.scrollHeight;
    console.log(`[${level.toUpperCase()}] ${message}`);
  }
  function clearConsole() {
    if (consoleOutput) {
      consoleOutput.innerHTML = "";
      logToConsole("\u{1F9F9} Console cleared", "info");
    }
  }
  document.addEventListener("DOMContentLoaded", async () => {
    let jobData = {};
    let resumeContent = "";
    const markdownEditor = document.getElementById("markdown-editor");
    const copyBtn = document.getElementById("copy-markdown");
    const generateReportBtn = document.getElementById("generate-report");
    const settingsBtn = document.getElementById("settings");
    const realtimeResponse = document.getElementById("realtime-response");
    const stopGenerationBtn = document.getElementById("stop-generation");
    const copyRealtimeBtn = document.getElementById("copy-realtime");
    const resumeUpload = document.getElementById("resume-upload");
    consoleOutput = document.getElementById("console-output");
    const clearConsoleBtn = document.getElementById("clear-console");
    if (!consoleOutput) {
      console.error("Console output element not found!");
    } else {
      logToConsole("\u{1F50D} Console monitor initialized", "info");
    }
    const propTitle = document.getElementById("prop-title");
    const propUrl = document.getElementById("prop-url");
    const propAuthor = document.getElementById("prop-author");
    const propPublished = document.getElementById("prop-published");
    const propCreated = document.getElementById("prop-created");
    const propDescription = document.getElementById("prop-description");
    const propTags = document.getElementById("prop-tags");
    const propHeadings = document.getElementById("prop-headings");
    const propImages = document.getElementById("prop-images");
    const propLocation = document.getElementById("prop-location");
    copyBtn.disabled = false;
    generateReportBtn.disabled = false;
    logToConsole("\u2705 Generate Report button enabled and ready", "success");
    generateReportBtn.style.opacity = "1";
    generateReportBtn.style.cursor = "pointer";
    setupToggleHandlers();
    setupAutoSave();
    setupSaveOnCollapse();
    const backendUrl = typeof JOBOPS_BACKEND_URL !== "undefined" ? JOBOPS_BACKEND_URL : "http://localhost:8877";
    chrome.storage.sync.set({ jobops_backend_url: backendUrl }, async () => {
      requestJobData();
    });
    chrome.runtime.onMessage.addListener(async (msg, _sender, _sendResponse) => {
      if (msg.action === "show_preview" && msg.jobData) {
        logToConsole("\u{1F4E8} Received preview data from content script", "info");
        logToConsole(`\u{1F4CA} Job title: ${msg.jobData.title || "N/A"}`, "info");
        jobData = msg.jobData;
        const jobExists = await jobOpsDataManager.checkAndLoadExistingJob(jobData.url);
        if (jobExists) {
          logToConsole("\u{1F504} Existing job application found and loaded", "info");
          showNotification2("\u{1F504} Existing job application loaded");
        } else {
          const { hasContent, missingSections, contentQuality } = checkRequiredSectionsContent();
          if (hasContent) {
            logToConsole(`\u{1F195} Creating new job application (Quality: ${contentQuality})`, "info");
            try {
              await jobOpsDataManager.createNewJobApplication(jobData);
              showNotification2(`\u{1F195} New job application created (${contentQuality} content)`);
              validateAndProvideFeedback(contentQuality, missingSections);
            } catch (error) {
              logToConsole(`\u274C Error creating job application: ${error}`, "error");
              showNotification2("\u274C Error creating job application", true);
            }
          } else {
            const minRequirements = missingSections.map((section) => {
              const req = [
                { name: "Position Details", minLength: 50 },
                { name: "Job Requirements", minLength: 50 },
                { name: "Company Information", minLength: 30 },
                { name: "Offer Details", minLength: 20 }
              ].find((s) => s.name === section);
              return `${section} (${req?.minLength || 50}+ chars)`;
            }).join(", ");
            logToConsole(`\u26A0\uFE0F Insufficient content for database creation. Missing: ${missingSections.join(", ")}`, "warning");
          }
        }
        populatePropertyFields(jobData);
        markdownEditor.value = generateMarkdown(jobData);
        copyBtn.disabled = false;
        generateReportBtn.disabled = false;
        logToConsole("\u2705 Preview data processed successfully", "success");
      }
    });
    if (resumeUpload) {
      console.log("Resume upload element found, adding event listener");
      resumeUpload.addEventListener("change", handleResumeUpload);
    } else {
      console.error("Resume upload element not found!");
    }
    generateReportBtn.addEventListener("click", (event) => {
      console.log("\u{1F3AF} GENERATE REPORT BUTTON CLICKED - DIRECT CONSOLE LOG");
      logToConsole("\u{1F3AF} Generate Report button clicked - event handler triggered", "info");
      generateReportBtn.style.transform = "scale(0.95)";
      setTimeout(() => {
        generateReportBtn.style.transform = "scale(1)";
      }, 100);
      handleGenerateReport();
    });
    settingsBtn.addEventListener("click", handleSettings);
    settingsBtn.addEventListener("contextmenu", handleTestAPI);
    if (clearConsoleBtn) {
      clearConsoleBtn.addEventListener("click", clearConsole);
    }
    if (stopGenerationBtn) {
      stopGenerationBtn.addEventListener("click", handleStopGeneration);
    }
    if (copyRealtimeBtn) {
      copyRealtimeBtn.addEventListener("click", handleCopyRealtime);
    }
    logToConsole("\u{1F680} JobOps Clipper initialized", "info");
    logToConsole("\u{1F4CB} Ready to process job postings and resumes", "success");
    document.documentElement.style.setProperty("--button-bottom", "48px");
    const form = document.querySelector("#properties-form");
    if (form) {
      form.style.paddingBottom = "80px";
    }
    const logToApplicationLog = (level, message, data) => {
      const logEntry = {
        timestamp: (/* @__PURE__ */ new Date()).toISOString(),
        level,
        component: "JobOpsClipper",
        message,
        correlation_id: `jobops_${Date.now()}`,
        user_id: "extension_user",
        request_id: `req_${Date.now()}`,
        ...data && { data }
      };
      console.log("APPLICATION_LOG:", JSON.stringify(logEntry));
    };
    function validateAndProvideFeedback(contentQuality, missingSections) {
      const guidance = getContentGuidance(contentQuality, missingSections);
      logToApplicationLog("INFO", "Content validation feedback provided", {
        contentQuality,
        missingSections,
        guidanceCount: guidance.length
      });
      guidance.forEach((tip) => {
        logToConsole(tip, "info");
      });
      if (contentQuality === "minimal" && missingSections.length > 0) {
        logToConsole("\u{1F50D} Tip: Expand the sections above to add more details", "info");
      } else if (contentQuality === "adequate") {
        logToConsole("\u2705 Good progress! Consider adding more specific examples", "success");
      } else if (contentQuality === "complete") {
        logToConsole("\u{1F389} Excellent! Your application is ready for comprehensive analysis", "success");
      }
    }
    logToApplicationLog("INFO", "JobOps Clipper extension initialized", {
      version: "1.0.0",
      database_ready: true,
      features: ["job_tracking", "database_storage", "ai_analysis"]
    });
    logToApplicationLog("INFO", "Debug console initialized in collapsed state", { initial_state: "collapsed" });
    async function saveSectionData(sectionName, data) {
      try {
        const jobInfo = getCurrentJobInfo();
        logToApplicationLog("INFO", `Saving section data`, {
          section: sectionName,
          job_application_id: jobInfo.id,
          canonical_url: jobInfo.url,
          data_keys: Object.keys(data)
        });
        switch (sectionName) {
          case "position_details":
            await jobOpsDataManager.savePositionDetails(data);
            break;
          case "job_requirements":
            await jobOpsDataManager.saveJobRequirements(data);
            break;
          case "company_information":
            await jobOpsDataManager.saveCompanyInformation(data);
            break;
          case "skills_matrix":
            await jobOpsDataManager.saveSkillsMatrix(data);
            break;
          case "application_materials":
            await jobOpsDataManager.saveApplicationMaterials(data);
            break;
          case "interview_schedule":
            await jobOpsDataManager.saveInterviewSchedule(data);
            break;
          case "interview_preparation":
            await jobOpsDataManager.saveInterviewPreparation(data);
            break;
          case "communication_log":
            await jobOpsDataManager.saveCommunicationLog(data);
            break;
          case "key_contacts":
            await jobOpsDataManager.saveKeyContacts(data);
            break;
          case "interview_feedback":
            await jobOpsDataManager.saveInterviewFeedback(data);
            break;
          case "offer_details":
            await jobOpsDataManager.saveOfferDetails(data);
            break;
          case "rejection_analysis":
            await jobOpsDataManager.saveRejectionAnalysis(data);
            break;
          case "privacy_policy":
            await jobOpsDataManager.savePrivacyPolicy(data);
            break;
          case "lessons_learned":
            await jobOpsDataManager.saveLessonsLearned(data);
            break;
          case "performance_metrics":
            await jobOpsDataManager.savePerformanceMetrics(data);
            break;
          case "advisor_review":
            await jobOpsDataManager.saveAdvisorReview(data);
            break;
          default:
            throw new Error(`Unknown section: ${sectionName}`);
        }
        logToApplicationLog("INFO", `Section data saved successfully`, {
          section: sectionName,
          job_application_id: jobInfo.id
        });
        logToConsole(`\u2705 ${sectionName} data saved successfully`, "success");
        showNotification2(`\u2705 ${sectionName} saved`);
      } catch (error) {
        const jobInfo = getCurrentJobInfo();
        logToApplicationLog("ERROR", `Failed to save section data`, {
          section: sectionName,
          job_application_id: jobInfo.id,
          error: error instanceof Error ? error.message : String(error)
        });
        logToConsole(`\u274C Error saving ${sectionName}: ${error}`, "error");
        showNotification2(`\u274C Error saving ${sectionName}`, true);
        throw error;
      }
    }
    function checkRequiredSectionsContent() {
      const requiredSections = [
        { name: "Position Details", id: "position-details", minLength: 50, adequateLength: 150 },
        { name: "Job Requirements", id: "job-requirements", minLength: 50, adequateLength: 150 },
        { name: "Company Information", id: "company-information", minLength: 30, adequateLength: 100 },
        { name: "Offer Details", id: "offer-details", minLength: 20, adequateLength: 80 }
      ];
      const missingSections = [];
      let hasContent = true;
      let totalContentLength = 0;
      let sectionsWithAdequateContent = 0;
      for (const section of requiredSections) {
        const sectionContent = getSectionContent(section.id);
        const contentLength = sectionContent.trim().length;
        totalContentLength += contentLength;
        if (contentLength < section.minLength) {
          missingSections.push(section.name);
          hasContent = false;
        } else if (contentLength >= section.adequateLength) {
          sectionsWithAdequateContent++;
        }
      }
      let contentQuality = "minimal";
      if (totalContentLength >= 500 && sectionsWithAdequateContent >= 2) {
        contentQuality = "adequate";
      }
      if (totalContentLength >= 800 && sectionsWithAdequateContent >= 3) {
        contentQuality = "complete";
      }
      logToApplicationLog("DEBUG", "Content validation completed", {
        totalContentLength,
        sectionsWithAdequateContent,
        missingSections,
        contentQuality,
        hasContent
      });
      return { hasContent, missingSections, contentQuality };
    }
    function getSectionContent(sectionId) {
      switch (sectionId) {
        case "position-details":
          return getTextareaValue("position-summary");
        case "job-requirements":
          return getTextareaValue("requirements-summary");
        case "company-information":
          return getTextareaValue("company-summary");
        case "offer-details":
          return getTextareaValue("offer-summary");
        case "markdown":
          return getTextareaValue("markdown-editor");
        default:
          return "";
      }
    }
    function getContentGuidance(contentQuality, missingSections) {
      const guidance = [];
      switch (contentQuality) {
        case "minimal":
          guidance.push("\u{1F4A1} Add more details to improve application quality");
          if (missingSections.includes("Position Details")) {
            guidance.push("\u{1F4DD} Include job title, company, location, salary range, and key responsibilities");
          }
          if (missingSections.includes("Job Requirements")) {
            guidance.push("\u{1F4CB} List required skills, experience level, education, and technical requirements");
          }
          if (missingSections.includes("Company Information")) {
            guidance.push("\u{1F3E2} Add company size, industry, mission, and recent news");
          }
          break;
        case "adequate":
          guidance.push("\u2705 Good content level - consider adding more specific details");
          break;
        case "complete":
          guidance.push("\u{1F389} Excellent content level - ready for comprehensive analysis");
          break;
      }
      return guidance;
    }
    function getInputValue(id) {
      const element = document.getElementById(id);
      return element ? element.value : "";
    }
    function getTextareaValue(id) {
      const element = document.getElementById(id);
      return element ? element.value : "";
    }
    function getSelectValue(id) {
      const element = document.getElementById(id);
      return element ? element.value : "";
    }
    function getCheckboxValue(id) {
      const element = document.getElementById(id);
      return element ? element.checked : false;
    }
    function collectAllFormData() {
      const formData = {
        positionDetails: {
          summary: getTextareaValue("position-summary")
        },
        jobRequirements: {
          summary: getTextareaValue("requirements-summary")
        },
        companyInformation: {
          summary: getTextareaValue("company-summary")
        },
        skillsMatrix: {
          summary: getTextareaValue("skills-assessment")
        },
        applicationMaterials: {
          summary: getTextareaValue("materials-summary")
        },
        interviewSchedule: {
          summary: getTextareaValue("interview-details")
        },
        interviewPreparation: {
          summary: getTextareaValue("preparation-summary")
        },
        communicationLog: {
          summary: getTextareaValue("communication-summary")
        },
        keyContacts: {
          summary: getTextareaValue("contacts-summary")
        },
        interviewFeedback: {
          summary: getTextareaValue("feedback-summary")
        },
        offerDetails: {
          summary: getTextareaValue("offer-summary")
        },
        rejectionAnalysis: {
          summary: getTextareaValue("rejection-summary")
        },
        privacyPolicy: {
          summary: getTextareaValue("privacy-summary")
        },
        lessonsLearned: {
          summary: getTextareaValue("lessons-summary")
        },
        performanceMetrics: {
          summary: getTextareaValue("metrics-summary")
        },
        advisorReview: {
          summary: getTextareaValue("advisor-summary")
        },
        applicationSummary: {
          summary: getTextareaValue("overall-summary")
        },
        markdownPreview: getTextareaValue("markdown-editor"),
        metadata: {
          url: getInputValue("prop-url"),
          title: getInputValue("prop-title"),
          author: getInputValue("prop-author"),
          published: getInputValue("prop-published"),
          created: getInputValue("prop-created"),
          description: getInputValue("prop-description"),
          tags: getInputValue("prop-tags"),
          location: getInputValue("prop-location")
        }
      };
      return formData;
    }
    function setupAutoSave() {
      const autoSaveFields = [propTitle, propUrl, propAuthor, propPublished, propCreated, propDescription, propTags, propLocation];
      autoSaveFields.forEach((field) => {
        let saveTimeout;
        field.addEventListener("input", () => {
          clearTimeout(saveTimeout);
          saveTimeout = setTimeout(async () => {
            try {
              updateJobDataFromFields();
              const { hasContent, missingSections, contentQuality } = checkRequiredSectionsContent();
              if (hasContent) {
                if (jobData.title || jobData.description || jobData.location) {
                  await saveSectionData("position_details", {
                    job_title: jobData.title,
                    job_description: jobData.description,
                    location: jobData.location,
                    source_url: jobData.url,
                    company_name: jobData.company || "",
                    salary_range: "",
                    employment_type: "",
                    experience_level: "",
                    remote_work_policy: ""
                  });
                }
                logToConsole("\u{1F4BE} Auto-saved job data to database", "debug");
              } else {
                logToConsole(`\u26A0\uFE0F Insufficient content for database save. Missing: ${missingSections.join(", ")}`, "debug");
              }
            } catch (error) {
              logToConsole(`\u274C Auto-save failed: ${error}`, "error");
            }
          }, 2e3);
        });
      });
    }
    function setupSaveOnCollapse() {
      const sections = [
        "position-details",
        "job-requirements",
        "company-information",
        "skills-matrix",
        "application-materials",
        "interview-schedule",
        "interview-preparation",
        "communication-log",
        "key-contacts",
        "interview-feedback",
        "offer-details",
        "rejection-analysis",
        "privacy-policy",
        "lessons-learned",
        "performance-metrics",
        "advisor-review",
        "application-summary"
      ];
      sections.forEach((sectionName) => {
        const sectionElement = document.querySelector(`[data-section="${sectionName}"]`);
        if (sectionElement) {
          const header = sectionElement.querySelector(".job-header");
          const content = sectionElement.querySelector(".job-content");
          if (header && content) {
            let wasExpanded = !content.classList.contains("collapsed");
            header.addEventListener("click", async (e) => {
              const previousState = wasExpanded;
              setTimeout(() => {
                wasExpanded = !content.classList.contains("collapsed");
                if (previousState && !wasExpanded) {
                  handleSectionSave(sectionName);
                }
              }, 50);
            });
          }
        }
      });
    }
    async function handleSectionSave(sectionName) {
      try {
        const sectionData = getSectionData(sectionName);
        const hasSectionContent = sectionData && Object.values(sectionData).some(
          (value) => typeof value === "string" && value.trim().length > 0
        );
        if (!hasSectionContent) {
          logToConsole(`\u{1F4BE} ${sectionName} is empty - no save needed`, "debug");
          return;
        }
        logToConsole(`\u{1F4BE} Saving ${sectionName}...`, "info");
        const { hasContent, missingSections, contentQuality } = checkRequiredSectionsContent();
        if (!hasContent) {
          const minRequirements = missingSections.map((section) => {
            const req = [
              { name: "Position Details", minLength: 50 },
              { name: "Job Requirements", minLength: 50 },
              { name: "Company Information", minLength: 30 },
              { name: "Offer Details", minLength: 20 }
            ].find((s) => s.name === section);
            return `${section} (${req?.minLength || 50}+ chars)`;
          }).join(", ");
          logToConsole(`\u26A0\uFE0F Cannot save - insufficient content. Missing: ${missingSections.join(", ")}`, "warning");
          return;
        }
        if (sectionData && Object.keys(sectionData).length > 0) {
          await saveSectionData(sectionName.replace("-", "_"), sectionData);
          logToConsole(`\u2705 ${sectionName} saved successfully`, "success");
        } else {
          logToConsole(`\u26A0\uFE0F No data to save for ${sectionName}`, "warning");
        }
      } catch (error) {
        logToConsole(`\u274C Failed to save ${sectionName}: ${error}`, "error");
        showNotification2(`\u274C Failed to save ${sectionName}`, true);
      }
    }
    function getSectionData(sectionName) {
      switch (sectionName) {
        case "position-details":
          return {
            summary: getTextareaValue("position-summary"),
            source_url: getInputValue("prop-url")
          };
        case "job-requirements":
          return {
            summary: getTextareaValue("requirements-summary")
          };
        case "company-information":
          return {
            summary: getTextareaValue("company-summary")
          };
        case "skills-matrix":
          return {
            summary: getTextareaValue("skills-assessment")
          };
        case "application-materials":
          return {
            summary: getTextareaValue("materials-summary")
          };
        case "interview-schedule":
          return {
            summary: getTextareaValue("interview-details")
          };
        case "interview-preparation":
          return {
            summary: getTextareaValue("preparation-summary")
          };
        case "communication-log":
          return {
            summary: getTextareaValue("communication-summary")
          };
        case "key-contacts":
          return {
            summary: getTextareaValue("contacts-summary")
          };
        case "interview-feedback":
          return {
            summary: getTextareaValue("feedback-summary")
          };
        case "offer-details":
          return {
            summary: getTextareaValue("offer-summary")
          };
        case "rejection-analysis":
          return {
            summary: getTextareaValue("rejection-summary")
          };
        case "privacy-policy":
          return {
            summary: getTextareaValue("privacy-summary")
          };
        case "lessons-learned":
          return {
            summary: getTextareaValue("lessons-summary")
          };
        case "performance-metrics":
          return {
            summary: getTextareaValue("metrics-summary")
          };
        case "advisor-review":
          return {
            summary: getTextareaValue("advisor-summary")
          };
        case "application-summary":
          return {
            summary: getTextareaValue("overall-summary")
          };
        default:
          return {};
      }
    }
    function getCurrentJobInfo() {
      return {
        id: jobOpsDataManager.getCurrentJobApplicationId(),
        url: jobOpsDataManager.getCurrentCanonicalUrl()
      };
    }
    async function updateJobStatus(status) {
      try {
        await jobOpsDataManager.updateJobStatus(status);
        logToConsole(`\u2705 Job status updated to: ${status}`, "success");
        showNotification2(`\u2705 Status updated to: ${status}`);
      } catch (error) {
        logToConsole(`\u274C Error updating job status: ${error}`, "error");
        showNotification2(`\u274C Error updating status`, true);
      }
    }
    function setupToggleHandlers() {
      const toggleHeaders = document.querySelectorAll(".properties-header, .markdown-header, .realtime-header, .job-header, .console-header");
      toggleHeaders.forEach((header) => {
        header.addEventListener("click", (event) => {
          if (event.target && event.target.closest("button")) {
            return;
          }
          const toggleTarget = header.getAttribute("data-toggle");
          if (toggleTarget) {
            toggleSection(toggleTarget);
          }
        });
      });
    }
    function toggleSection(sectionId) {
      const content = document.getElementById(sectionId);
      if (!content) {
        logToConsole(`\u274C Section element not found: ${sectionId}`, "error");
        return;
      }
      const header = content.parentElement?.querySelector('[data-toggle="' + sectionId + '"]');
      const toggleIcon = header?.querySelector(".toggle-icon");
      if (content && header && toggleIcon) {
        const isCollapsed = content.classList.contains("collapsed");
        if (isCollapsed) {
          content.classList.remove("collapsed");
          content.classList.add("expanded");
          if (sectionId === "console-output") {
            toggleIcon.textContent = "\u25BC";
            const consoleMonitor = content.closest(".console-monitor");
            if (consoleMonitor) {
              consoleMonitor.setAttribute("data-collapsed", "false");
              document.documentElement.style.setProperty("--button-bottom", "208px");
              const form2 = document.querySelector("#properties-form");
              if (form2) {
                form2.style.paddingBottom = "120px";
              }
            }
            logToApplicationLog("INFO", "Debug console expanded", { section: sectionId });
          } else {
            toggleIcon.textContent = "\u25BC";
          }
          logToConsole(`\u2705 Section expanded: ${sectionId}`, "debug");
        } else {
          content.classList.remove("expanded");
          content.classList.add("collapsed");
          if (sectionId === "console-output") {
            toggleIcon.textContent = "\u25B6";
            const consoleMonitor = content.closest(".console-monitor");
            if (consoleMonitor) {
              consoleMonitor.setAttribute("data-collapsed", "true");
              document.documentElement.style.setProperty("--button-bottom", "48px");
              const form2 = document.querySelector("#properties-form");
              if (form2) {
                form2.style.paddingBottom = "80px";
              }
            }
            logToApplicationLog("INFO", "Debug console collapsed", { section: sectionId });
          } else {
            toggleIcon.textContent = "\u25B6";
          }
          logToConsole(`\u2705 Section collapsed: ${sectionId}`, "debug");
        }
      } else {
        logToConsole(`\u274C Header or toggle icon not found for section: ${sectionId}`, "error");
      }
    }
    function populatePropertyFields(data) {
      propTitle.value = data.title || "";
      propUrl.value = data.url || "";
      propAuthor.value = data.author || "";
      propPublished.value = data.published || "";
      propCreated.value = data.created_at || "";
      propDescription.value = data.description || "";
      propTags.value = Array.isArray(data.metaKeywords) ? data.metaKeywords.join(", ") : data.metaKeywords || "";
      propLocation.value = data.location || "";
      propHeadings.innerHTML = "";
      if (Array.isArray(data.headings) && data.headings.length > 0) {
        for (const h of data.headings) {
          const tag = document.createElement("span");
          tag.className = "property-tag";
          tag.textContent = h.text + (h.tag ? ` (${h.tag})` : "");
          propHeadings.appendChild(tag);
        }
      }
      propImages.innerHTML = "";
      if (Array.isArray(data.images) && data.images.length > 0) {
        const imageCount = document.createElement("div");
        imageCount.className = "property-image-count";
        imageCount.textContent = `\u{1F5BC}\uFE0F ${data.images.length} images (not loaded)`;
        imageCount.title = "Images skipped for performance";
        propImages.appendChild(imageCount);
        logToConsole(`\u{1F5BC}\uFE0F Skipped loading ${data.images.length} images for generate-report workflow`, "info");
      }
    }
    function updateJobDataFromFields() {
      jobData.title = propTitle.value;
      jobData.url = propUrl.value;
      jobData.author = propAuthor.value;
      jobData.published = propPublished.value;
      jobData.created_at = propCreated.value;
      jobData.description = propDescription.value;
      jobData.metaKeywords = propTags.value.split(",").map((t) => t.trim()).filter(Boolean);
      jobData.location = propLocation.value;
      markdownEditor.value = generateMarkdown(jobData);
    }
    [propTitle, propUrl, propAuthor, propPublished, propCreated, propDescription, propTags, propLocation].forEach((input) => {
      input.addEventListener("input", updateJobDataFromFields);
    });
    async function requestJobData() {
      logToConsole("\u{1F310} Requesting job data from current page...", "info");
      chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        if (!tabs[0]?.id) {
          logToConsole("\u274C No active tab found", "error");
          return;
        }
        logToConsole("\u{1F50D} Checking content script availability...", "debug");
        chrome.scripting.executeScript(
          {
            target: { tabId: tabs[0].id },
            func: () => !!window && !!window.document && !!window.document.body
          },
          async (results) => {
            if (chrome.runtime.lastError || !results || !results[0].result) {
              logToConsole("\u274C Content script not loaded. Please refresh the page and try again.", "error");
              return;
            }
            logToConsole("\u2705 Content script available, requesting page data...", "success");
            chrome.tabs.sendMessage(
              tabs[0].id,
              { action: "clip_page" },
              async (response) => {
                if (chrome.runtime.lastError) {
                  logToConsole("\u274C Could not connect to content script. Try refreshing the page.", "error");
                  return;
                }
                if (response && response.jobData) {
                  logToConsole("\u2705 Job data received successfully!", "success");
                  logToConsole(`\u{1F4CA} Job title: ${response.jobData.title || "N/A"}`, "info");
                  logToConsole(`\u{1F4CB} Job data keys: ${Object.keys(response.jobData).join(", ")}`, "debug");
                  if (!response.jobData.title && !response.jobData.body) {
                    logToConsole("\u26A0\uFE0F Job data missing essential fields (title/body)", "warning");
                    showNotification2("\u26A0\uFE0F Job data incomplete. Please refresh the page and try again.", true);
                    return;
                  }
                  jobData = response.jobData;
                  const jobExists = await jobOpsDataManager.checkAndLoadExistingJob(jobData.url);
                  if (jobExists) {
                    logToConsole("\u{1F504} Existing job application found and loaded", "info");
                    showNotification2("\u{1F504} Existing job application loaded");
                  } else {
                    const { hasContent, missingSections, contentQuality } = checkRequiredSectionsContent();
                    if (hasContent) {
                      logToConsole(`\u{1F195} Creating new job application (Quality: ${contentQuality})`, "info");
                      try {
                        await jobOpsDataManager.createNewJobApplication(jobData);
                        showNotification2(`\u{1F195} New job application created (${contentQuality} content)`);
                        validateAndProvideFeedback(contentQuality, missingSections);
                      } catch (error) {
                        logToConsole(`\u274C Error creating job application: ${error}`, "error");
                        showNotification2("\u274C Error creating job application", true);
                      }
                    } else {
                      const minRequirements = missingSections.map((section) => {
                        const req = [
                          { name: "Position Details", minLength: 50 },
                          { name: "Job Requirements", minLength: 50 },
                          { name: "Company Information", minLength: 30 },
                          { name: "Offer Details", minLength: 20 }
                        ].find((s) => s.name === section);
                        return `${section} (${req?.minLength || 50}+ chars)`;
                      }).join(", ");
                      logToConsole(`\u26A0\uFE0F Insufficient content for database creation. Missing: ${missingSections.join(", ")}`, "warning");
                    }
                  }
                  populatePropertyFields(jobData);
                  markdownEditor.value = generateMarkdown(jobData);
                  copyBtn.disabled = false;
                  logToConsole("\u2705 Job data populated successfully", "success");
                } else {
                  logToConsole("\u26A0\uFE0F No job data received from content script", "warning");
                  showNotification2("\u26A0\uFE0F No job data found. Please refresh the page and try again.", true);
                }
              }
            );
          }
        );
      });
    }
    copyBtn.onclick = async () => {
      logToConsole("\u{1F4CB} Copy to clipboard triggered", "info");
      try {
        const allFormData = collectAllFormData();
        const hasContent = Object.values(allFormData).some((section) => {
          if (typeof section === "string") {
            return section.trim().length > 0;
          } else if (typeof section === "object" && section !== null) {
            return Object.values(section).some((value) => {
              if (typeof value === "string") {
                return value.trim().length > 0;
              } else if (typeof value === "boolean") {
                return value;
              }
              return false;
            });
          }
          return false;
        });
        if (!hasContent) {
          logToConsole("\u274C No content to copy", "error");
          showNotification2("No content to copy!", true);
          return;
        }
        const jsonContent = JSON.stringify(allFormData, null, 2);
        logToConsole(`\u{1F4CB} Copying JSON data (${jsonContent.length} characters) to clipboard...`, "progress");
        await navigator.clipboard.writeText(jsonContent);
        logToConsole("\u2705 All form data copied to clipboard as JSON!", "success");
        showNotification2("\u2705 All form data copied as JSON!");
      } catch (e) {
        logToConsole(`\u274C Copy failed: ${e}`, "error");
        showNotification2("\u274C Failed to copy to clipboard", true);
      }
    };
    function showNotification2(message, isError = false) {
      if (chrome.notifications) {
        chrome.notifications.create({
          type: "basic",
          iconUrl: "icon.png",
          title: "JobOps Clipper",
          message,
          priority: isError ? 2 : 1
        });
      } else {
        logToConsole(message, isError ? "error" : "info");
      }
    }
    async function handleResumeUpload(event) {
      console.log("\u{1F3AF} RESUME UPLOAD TRIGGERED - DIRECT CONSOLE LOG");
      logToConsole("\u{1F4C1} Resume upload triggered", "info");
      const target = event.target;
      const file = target.files?.[0];
      if (!file) {
        logToConsole("\u274C No file selected", "error");
        showNotification2("No file selected", true);
        return;
      }
      if (file.type !== "application/pdf") {
        logToConsole("\u274C Invalid file type - PDF required", "error");
        showNotification2("Please select a PDF file", true);
        return;
      }
      logToConsole(`\u{1F4C4} Starting PDF extraction: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`, "progress");
      try {
        logToConsole("\u{1F4C4} Loading PDF file...", "progress");
        showNotification2("\u{1F4C4} Loading PDF file...");
        logToConsole("\u{1F4C4} Loading PDF file into memory...", "progress");
        logToConsole("\u{1F50D} Extracting text content from PDF...", "progress");
        showNotification2("\u{1F50D} Extracting PDF content...");
        logToConsole("\u{1F50D} Extracting text content from PDF...", "progress");
        console.log("\u{1F3AF} ABOUT TO EXTRACT PDF CONTENT - DIRECT CONSOLE LOG");
        resumeContent = await extractPdfContent(file);
        console.log("\u{1F3AF} PDF EXTRACTION COMPLETED - DIRECT CONSOLE LOG");
        logToConsole(`\u2705 PDF extraction completed! Content length: ${resumeContent.length} characters`, "success");
        logToConsole(`\u{1F4C4} Resume content preview: ${resumeContent.substring(0, 200)}${resumeContent.length > 200 ? "..." : ""}`, "debug");
        logToConsole(`\u{1F4C4} Resume content stored in variable: ${resumeContent ? "YES" : "NO"}`, "debug");
        logToConsole("\u2705 Resume content extracted successfully!", "success");
        logToConsole("\u{1F4CB} Resume ready for report generation", "success");
        setTimeout(() => {
          logToConsole("\u{1F4CB} Resume ready for report generation", "success");
        }, 2e3);
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : String(error);
        logToConsole(`\u274C PDF extraction failed: ${errorMessage}`, "error");
        showNotification2(`\u274C Failed to extract PDF content: ${errorMessage}`, true);
      }
    }
    async function handleGenerateReport() {
      console.log("\u{1F3AF} GENERATE REPORT BUTTON CLICKED - DIRECT CONSOLE LOG");
      logToConsole("\u{1F680} Generate Report button clicked", "info");
      logToConsole(`\u{1F4CA} Current resumeContent length: ${resumeContent.length}`, "debug");
      logToConsole(`\u{1F4CB} Current jobData keys: ${Object.keys(jobData).join(", ")}`, "debug");
      if (!resumeContent) {
        logToConsole("\u{1F4C1} No resume content found, triggering file upload", "warning");
        resumeUpload.click();
        return;
      }
      if (!jobData || Object.keys(jobData).length === 0) {
        logToConsole("\u{1F4CB} No job data found, requesting from current page", "warning");
        await new Promise((resolve) => {
          requestJobData();
          setTimeout(() => {
            logToConsole(`\u{1F4CB} After requestJobData - jobData keys: ${Object.keys(jobData).join(", ")}`, "debug");
            logToConsole(`\u{1F4CB} Job data title: ${jobData.title || "N/A"}`, "debug");
            logToConsole(`\u{1F4CB} Job data body length: ${jobData.body ? jobData.body.length : 0}`, "debug");
            resolve();
          }, 1e3);
        });
        if (!jobData || Object.keys(jobData).length === 0) {
          logToConsole("\u274C Still no job data after request, cannot proceed", "error");
          showNotification2("\u274C No job data available. Please refresh the page and try again.", true);
          return;
        }
      }
      if (!jobData.title && !jobData.body) {
        logToConsole("\u274C Job data missing essential fields (title/body)", "error");
        showNotification2("\u274C Job data incomplete. Please refresh the page and try again.", true);
        return;
      }
      logToConsole("\u{1F680} Starting report generation process", "info");
      generateReportBtn.disabled = true;
      logToConsole("\u{1F504} Starting report generation...", "info");
      showNotification2("\u{1F504} Starting report generation...");
      logToConsole("\u{1F3AF} BUTTON CLICK VERIFICATION - This should appear immediately", "info");
      try {
        logToConsole("\u{1F511} Checking API configuration...", "progress");
        logToConsole("\u{1F511} Checking API configuration...", "info");
        const apiKey = await getGroqApiKey();
        if (!apiKey) {
          throw new Error("Groq API key not configured");
        }
        logToConsole("\u2705 API key found, proceeding with report generation", "success");
        showNotification2("\u2705 API key found, proceeding...");
        logToConsole("\u{1F4CA} Preparing job data and resume content...", "progress");
        logToConsole(`\u{1F4CB} Job data keys: ${Object.keys(jobData).join(", ")}`, "debug");
        logToConsole(`\u{1F4C4} Resume content length: ${resumeContent.length} characters`, "debug");
        logToConsole("\u{1F4CA} Preparing data for analysis...", "info");
        logToConsole("\u{1F916} Starting streaming report generation...", "progress");
        logToConsole("\u{1F916} Starting streaming report generation...", "info");
        logToConsole("\u{1F916} Starting streaming analysis...", "info");
        logToConsole("\u{1F527} Forcing real-time section expansion...", "debug");
        const realtimeContent = document.getElementById("realtime-content");
        if (realtimeContent) {
          if (realtimeContent.classList.contains("collapsed")) {
            toggleSection("realtime-content");
            logToConsole("\u2705 Real-time section expanded", "debug");
          } else {
            logToConsole("\u2705 Real-time section already expanded", "debug");
          }
        } else {
          logToConsole("\u274C Real-time content element not found", "error");
        }
        const realtimeResponse2 = document.getElementById("realtime-response");
        if (realtimeResponse2) {
          realtimeResponse2.innerHTML = '<span class="typing-text">\u{1F680} Starting report generation...</span>';
          realtimeResponse2.classList.add("typing");
          logToConsole("\u2705 Real-time response element initialized with test message", "debug");
        } else {
          logToConsole("\u274C Real-time response element not found", "error");
        }
        if (stopGenerationBtn) {
          stopGenerationBtn.style.display = "inline-block";
          logToConsole("\u2705 Stop generation button shown", "debug");
        } else {
          logToConsole("\u274C Stop generation button not found", "error");
        }
        isGenerating = true;
        abortController = new AbortController();
        logToConsole("\u{1F504} Calling generateJobReportStreaming...", "debug");
        const report = await generateJobReportStreaming(jobData, resumeContent, (chunk) => {
          logToConsole(`\u{1F4DD} Chunk callback received: ${chunk.length} characters`, "debug");
          const realtimeResponse3 = document.getElementById("realtime-response");
          if (realtimeResponse3) {
            const span = document.createElement("span");
            span.className = "typing-text";
            span.textContent = chunk;
            realtimeResponse3.appendChild(span);
            realtimeResponse3.scrollTop = realtimeResponse3.scrollHeight;
            logToConsole(`\u{1F4DD} Real-time chunk added to UI: ${chunk.length} characters`, "debug");
          } else {
            logToConsole("\u274C Real-time response element not found in chunk callback", "error");
          }
        });
        logToConsole(`\u{1F4CA} Report generation result: ${report ? "success" : "failed"}`, "debug");
        if (!report) {
          throw new Error("No report generated - API returned empty response");
        }
        logToConsole("\u2705 Report generated successfully!", "success");
        logToConsole("\u{1F4CB} Report ready for copying", "success");
        markdownEditor.value = report;
        if (realtimeResponse2) {
          realtimeResponse2.classList.remove("typing");
          logToConsole("\u2705 Real-time response completed", "success");
        }
        setTimeout(() => {
          logToConsole("\u{1F4CB} Report ready for copying", "success");
        }, 2e3);
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : String(error);
        logToConsole(`\u274C Report generation failed: ${errorMessage}`, "error");
        isGenerating = false;
        abortController = null;
        const realtimeResponse2 = document.getElementById("realtime-response");
        if (realtimeResponse2) {
          realtimeResponse2.classList.remove("typing");
          realtimeResponse2.innerHTML += `<br><span style="color: #ff6b6b;">\u274C Error: ${errorMessage}</span>`;
          logToConsole("\u2705 Error message added to real-time response", "debug");
        }
        if (stopGenerationBtn) {
          stopGenerationBtn.style.display = "none";
        }
        if (errorMessage.includes("API key")) {
          logToConsole("\u{1F527} API key required - please configure in settings", "warning");
          showNotification2("\u274C Groq API key not configured. Click \u2699\uFE0F to set it up.", true);
        } else if (errorMessage.includes("Groq API")) {
          logToConsole("\u26A0\uFE0F Groq API failed, trying Ollama fallback...", "warning");
          showNotification2("\u26A0\uFE0F Groq API failed, trying Ollama...");
          try {
            logToConsole("\u{1F504} Attempting Ollama fallback...", "progress");
            const report = await generateJobReportWithOllama(jobData, resumeContent);
            markdownEditor.value = report;
            logToConsole("\u2705 Report generated with Ollama fallback!", "success");
            showNotification2("\u2705 Report generated with Ollama fallback!");
          } catch (ollamaError) {
            logToConsole("\u274C Both Groq and Ollama failed", "error");
            showNotification2("\u274C Report generation failed on all services", true);
          }
        } else {
          logToConsole("\u274C Report generation failed with unknown error", "error");
          showNotification2("\u274C Report generation failed", true);
        }
      } finally {
        generateReportBtn.disabled = false;
        isGenerating = false;
        abortController = null;
        if (realtimeResponse) {
          realtimeResponse.classList.remove("typing");
        }
        if (stopGenerationBtn) {
          stopGenerationBtn.style.display = "none";
        }
      }
    }
    async function handleSettings() {
      logToConsole("\u2699\uFE0F Settings dialog opened", "info");
      const apiKey = await getGroqApiKey();
      const newApiKey = prompt("Enter your Groq API key (leave empty to remove):", apiKey || "");
      if (newApiKey !== null) {
        if (newApiKey.trim()) {
          logToConsole("\u{1F511} Saving new Groq API key...", "progress");
          await new Promise((resolve) => {
            chrome.storage.sync.set({ groq_api_key: newApiKey.trim() }, () => {
              logToConsole("\u2705 Groq API key saved successfully!", "success");
              showNotification2("\u2705 Groq API key saved!");
              resolve();
            });
          });
        } else {
          logToConsole("\u{1F5D1}\uFE0F Removing Groq API key...", "warning");
          await new Promise((resolve) => {
            chrome.storage.sync.remove(["groq_api_key"], () => {
              logToConsole("\u2705 Groq API key removed successfully!", "success");
              showNotification2("\u2705 Groq API key removed!");
              resolve();
            });
          });
        }
      } else {
        logToConsole("\u274C Settings dialog cancelled", "info");
      }
    }
    async function handleTestAPI(event) {
      event.preventDefault();
      logToConsole("\u{1F9EA} Testing API connectivity...", "info");
      try {
        const apiKey = await getGroqApiKey();
        if (!apiKey) {
          logToConsole("\u274C No API key configured", "error");
          showNotification2("\u274C No API key configured", true);
          return;
        }
        logToConsole("\u{1F511} API key found, testing Groq API...", "progress");
        const testResponse = await callGroqAPI("Say 'Hello, API test successful!'", (chunk) => {
          logToConsole(`\u{1F9EA} Test chunk: ${chunk}`, "debug");
        });
        if (testResponse) {
          logToConsole("\u2705 API test successful!", "success");
          showNotification2("\u2705 API test successful!");
        } else {
          logToConsole("\u274C API test failed - no response", "error");
          showNotification2("\u274C API test failed", true);
        }
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : String(error);
        logToConsole(`\u274C API test failed: ${errorMessage}`, "error");
        showNotification2(`\u274C API test failed: ${errorMessage}`, true);
      }
    }
  });
  function generateMarkdown(jobData) {
    let md = "";
    if (jobData.title)
      md += `# ${jobData.title}
`;
    if (jobData.body)
      md += `
${jobData.body}
`;
    if (jobData.location)
      md += `
**Location:** ${jobData.location}
`;
    if (jobData.metaKeywords && Array.isArray(jobData.metaKeywords) && jobData.metaKeywords.length > 0) {
      md += `
## Tags
`;
      md += jobData.metaKeywords.map((kw) => `**${kw}**`).join(" ");
      md += "\n";
    }
    const skipKeys = /* @__PURE__ */ new Set(["title", "body", "metaKeywords", "headings", "images"]);
    for (const [key, value] of Object.entries(jobData)) {
      if (skipKeys.has(key))
        continue;
      if (typeof value === "string" && value.trim() !== "") {
        md += `
## ${key.charAt(0).toUpperCase() + key.slice(1)}
${value}
`;
      } else if (Array.isArray(value) && value.length > 0) {
        md += `
## ${key.charAt(0).toUpperCase() + key.slice(1)}
`;
        md += value.map((v) => `- ${typeof v === "string" ? v : JSON.stringify(v)}`).join("\n");
        md += "\n";
      }
    }
    if (jobData.url)
      md += `
[Source](${jobData.url})
`;
    return md;
  }
  async function extractPdfContent(file) {
    return new Promise((resolve, reject) => {
      logToConsole("\u{1F504} Starting PDF content extraction...", "progress");
      const reader = new FileReader();
      reader.onload = async function(e) {
        try {
          logToConsole("\u{1F4D6} File read successfully, creating typed array...", "debug");
          const typedarray = new Uint8Array(e.target?.result);
          logToConsole(`\u{1F4CA} Typed array created, size: ${typedarray.length} bytes`, "debug");
          const header = new TextDecoder().decode(typedarray.slice(0, 10));
          logToConsole(`\u{1F4C4} File header: ${header}`, "debug");
          if (!header.includes("%PDF")) {
            logToConsole("\u26A0\uFE0F File doesn't appear to be a valid PDF", "warning");
          }
          try {
            const pdfjsLib = window["pdfjs-dist/build/pdf"];
            if (pdfjsLib) {
              logToConsole("\u2705 PDF.js available, using it for extraction...", "success");
              extractPdfWithLibrary(typedarray, resolve, reject);
              return;
            }
          } catch (error) {
            logToConsole(`\u26A0\uFE0F PDF.js method failed: ${error}`, "warning");
          }
          logToConsole("\u{1F4DA} PDF.js not available, trying to load from multiple sources...", "progress");
          const status = document.getElementById("clip-status");
          if (status) {
            status.textContent = "\u{1F4DA} Loading PDF processing library...";
            status.className = "loading";
          }
          const cdnSources = [
            "https://unpkg.com/pdfjs-dist@3.11.174/build/pdf.min.js",
            "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js",
            "https://cdn.jsdelivr.net/npm/pdfjs-dist@3.11.174/build/pdf.min.js"
          ];
          let loaded = false;
          const timeout = setTimeout(() => {
            if (!loaded) {
              logToConsole("\u23F0 PDF.js loading timeout, using fallback method", "warning");
              const fallbackText = extractPdfFallback(typedarray);
              if (fallbackText && fallbackText.length > 50) {
                resolve(fallbackText);
              } else {
                const manualText = prompt("PDF extraction failed. Please paste your resume content manually:");
                if (manualText && manualText.trim().length > 10) {
                  resolve(manualText.trim());
                } else {
                  reject(new Error("No resume content available"));
                }
              }
            }
          }, 1e4);
          for (const source of cdnSources) {
            if (loaded)
              break;
            try {
              logToConsole(`\u{1F4DA} Trying to load PDF.js from: ${source}`, "debug");
              const script = document.createElement("script");
              script.src = source;
              script.onload = () => {
                if (!loaded) {
                  loaded = true;
                  clearTimeout(timeout);
                  logToConsole(`\u2705 PDF.js loaded from ${source}`, "success");
                  extractPdfWithLibrary(typedarray, resolve, reject);
                }
              };
              script.onerror = () => {
                logToConsole(`\u274C Failed to load PDF.js from ${source}`, "debug");
              };
              document.head.appendChild(script);
              await new Promise((resolve2) => setTimeout(resolve2, 2e3));
            } catch (error) {
              logToConsole(`\u274C Error loading from ${source}: ${error}`, "debug");
            }
          }
          if (!loaded) {
            logToConsole("\u26A0\uFE0F All PDF.js sources failed, using fallback method...", "warning");
            const fallbackText = extractPdfFallback(typedarray);
            if (fallbackText && fallbackText.length > 50) {
              logToConsole("\u2705 Fallback PDF extraction successful", "success");
              resolve(fallbackText);
            } else {
              logToConsole("\u274C All PDF extraction methods failed, using manual input", "warning");
              const manualText = prompt("PDF extraction failed. Please paste your resume content manually:");
              if (manualText && manualText.trim().length > 10) {
                logToConsole("\u2705 Manual resume content provided", "success");
                resolve(manualText.trim());
              } else {
                logToConsole("\u274C No manual content provided", "error");
                reject(new Error("No resume content available"));
              }
            }
          }
        } catch (error) {
          logToConsole(`\u274C Error in PDF extraction: ${error}`, "error");
          reject(error);
        }
      };
      reader.onerror = (error) => {
        logToConsole(`\u274C FileReader error: ${error}`, "error");
        reject(new Error("Failed to read file"));
      };
      reader.readAsArrayBuffer(file);
    });
  }
  function extractPdfFallback(typedarray) {
    try {
      logToConsole("\u{1F504} Using fallback PDF extraction method...", "progress");
      const decoder = new TextDecoder("utf-8");
      const text = decoder.decode(typedarray);
      const textMatches = text.match(/\(([^)]+)\)/g);
      if (textMatches && textMatches.length > 0) {
        const extractedText = textMatches.map((match) => match.slice(1, -1)).filter((text2) => text2.length > 3 && !text2.match(/^[0-9\s]+$/)).join(" ");
        if (extractedText.length > 50) {
          logToConsole(`\u2705 Fallback extraction found ${extractedText.length} characters`, "success");
          return extractedText;
        }
      }
      const readableText = text.match(/[A-Za-z\s]{10,}/g);
      if (readableText && readableText.length > 0) {
        const combined = readableText.join(" ").trim();
        if (combined.length > 50) {
          logToConsole(`\u2705 Fallback extraction found ${combined.length} characters`, "success");
          return combined;
        }
      }
      logToConsole("\u26A0\uFE0F Fallback extraction found minimal text", "warning");
      return "PDF content could not be extracted. Please ensure the PDF contains text (not just images).";
    } catch (error) {
      logToConsole(`\u274C Fallback extraction failed: ${error}`, "error");
      return "PDF extraction failed. Please try a different PDF file.";
    }
  }
  async function extractPdfWithLibrary(typedarray, resolve, reject) {
    try {
      logToConsole("\u{1F504} Starting PDF library extraction...", "progress");
      const pdfjsLib = window["pdfjs-dist/build/pdf"];
      if (!pdfjsLib) {
        throw new Error("PDF.js library not available");
      }
      const status = document.getElementById("clip-status");
      if (status) {
        status.textContent = "\u{1F4D6} Loading PDF document...";
        status.className = "loading";
      }
      logToConsole("\u{1F4D6} Creating PDF document from typed array...", "progress");
      const loadingTask = pdfjsLib.getDocument({ data: typedarray });
      const pdf = await loadingTask.promise;
      logToConsole(`\u{1F4C4} PDF document loaded, pages: ${pdf.numPages}`, "success");
      let fullText = "";
      const totalPages = pdf.numPages;
      for (let i = 1; i <= totalPages; i++) {
        logToConsole(`\u{1F4C4} Processing page ${i} of ${totalPages}...`, "progress");
        const status2 = document.getElementById("clip-status");
        if (status2) {
          status2.textContent = `\u{1F4C4} Processing page ${i} of ${totalPages}...`;
          status2.className = "loading";
        }
        const page = await pdf.getPage(i);
        const textContent = await page.getTextContent();
        const pageText = textContent.items.map((item) => item.str).join(" ");
        fullText += pageText + "\n";
        logToConsole(`\u2705 Page ${i} processed, text length: ${pageText.length} characters`, "debug");
      }
      logToConsole(`\u{1F389} PDF extraction completed! Total text length: ${fullText.length} characters`, "success");
      resolve(fullText.trim());
    } catch (error) {
      logToConsole(`\u274C Error in PDF library extraction: ${error}`, "error");
      reject(new Error(`PDF extraction failed: ${error}`));
    }
  }
  async function generateJobReportStreaming(jobData, resumeContent, onChunk) {
    const cleanJobData = { ...jobData };
    if (cleanJobData.images) {
      delete cleanJobData.images;
    }
    const prompt2 = `You are an expert job application analyst. Based on the provided job posting data and resume content, generate a comprehensive job application tracking report.

Job Posting Data:
${JSON.stringify(cleanJobData, null, 2)}

Resume Content:
${resumeContent}

Please analyze this information and fill out the job application tracking report template. Extract all relevant information from both the job posting and resume to populate the template fields. Use your analysis to:

1. Identify skills matches and gaps
2. Suggest interview preparation strategies
3. Provide actionable insights for the application process
4. Create realistic timelines and goals
5. Offer specific recommendations for improvement

Fill in all template placeholders with concrete, actionable information based on the provided data.`;
    try {
      logToConsole("\u{1F916} Attempting Groq API with streaming...", "progress");
      const groqResponse = await callGroqAPI(prompt2, onChunk);
      if (groqResponse) {
        logToConsole("\u2705 Groq API succeeded with streaming", "success");
        return groqResponse;
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error);
      logToConsole(`\u26A0\uFE0F Groq API failed: ${errorMessage}`, "warning");
      logToConsole("\u{1F504} Falling back to Ollama...", "progress");
      try {
        logToConsole("\u{1F916} Attempting Ollama API fallback...", "progress");
        const ollamaResponse = await callOllamaAPI(prompt2);
        if (ollamaResponse) {
          logToConsole("\u2705 Ollama API succeeded", "success");
          return ollamaResponse;
        }
      } catch (ollamaError) {
        const ollamaErrorMessage = ollamaError instanceof Error ? ollamaError.message : String(ollamaError);
        logToConsole(`\u274C Ollama API also failed: ${ollamaErrorMessage}`, "error");
      }
    }
    logToConsole("\u274C Both Groq and Ollama APIs failed", "error");
    throw new Error("Both Groq and Ollama APIs failed");
  }
  async function generateJobReportWithOllama(jobData, resumeContent) {
    const cleanJobData = { ...jobData };
    if (cleanJobData.images) {
      delete cleanJobData.images;
    }
    const prompt2 = `You are an expert job application analyst. Based on the provided job posting data and resume content, generate a comprehensive job application tracking report.

Job Posting Data:
${JSON.stringify(cleanJobData, null, 2)}

Resume Content:
${resumeContent}

Please analyze this information and fill out the job application tracking report template. Extract all relevant information from both the job posting and resume to populate the template fields. Use your analysis to:

1. Identify skills matches and gaps
2. Suggest interview preparation strategies
3. Provide actionable insights for the application process
4. Create realistic timelines and goals
5. Offer specific recommendations for improvement

Fill in all template placeholders with concrete, actionable information based on the provided data.`;
    const ollamaResponse = await callOllamaAPI(prompt2);
    if (ollamaResponse) {
      return ollamaResponse;
    }
    throw new Error("Ollama API failed");
  }
  async function callGroqAPI(prompt2, onChunk) {
    try {
      logToConsole("\u{1F511} Retrieving Groq API key from storage...", "debug");
      const apiKey = await getGroqApiKey();
      if (!apiKey) {
        logToConsole("\u274C No Groq API key found in storage", "error");
        throw new Error("Groq API key not configured");
      }
      logToConsole("\u2705 Groq API key retrieved successfully", "debug");
      logToConsole(`\u{1F310} Preparing request to Groq API: ${GROQ_API_URL}`, "debug");
      logToConsole(`\u{1F916} Using model: ${GROQ_MODEL}`, "debug");
      logToConsole(`\u{1F4DD} Prompt length: ${prompt2.length} characters`, "debug");
      const requestBody = {
        model: GROQ_MODEL,
        messages: [
          {
            role: "system",
            content: "You are an expert job application analyst and career advisor. Provide comprehensive, actionable insights and fill out templates completely."
          },
          {
            role: "user",
            content: prompt2
          }
        ],
        temperature: 0.3,
        max_tokens: 4e3,
        stream: onChunk ? true : false
      };
      logToConsole("\u{1F4E4} Sending request to Groq API...", "debug");
      logToConsole(`\u{1F4CA} Request payload size: ${JSON.stringify(requestBody).length} characters`, "debug");
      logToConsole(`\u{1F504} Streaming mode: ${onChunk ? "enabled" : "disabled"}`, "debug");
      const startTime = Date.now();
      const response = await fetch(GROQ_API_URL, {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${apiKey}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify(requestBody),
        signal: abortController?.signal
      });
      const endTime = Date.now();
      const responseTime = endTime - startTime;
      logToConsole(`\u23F1\uFE0F Response received in ${responseTime}ms`, "debug");
      logToConsole(`\u{1F4E1} HTTP Status: ${response.status} ${response.statusText}`, "debug");
      logToConsole(`\u{1F4CB} Response headers: ${JSON.stringify(Object.fromEntries(response.headers.entries()))}`, "debug");
      if (!response.ok) {
        const errorText = await response.text();
        logToConsole(`\u274C Groq API error response: ${errorText}`, "error");
        throw new Error(`Groq API error: ${response.status} ${response.statusText} - ${errorText}`);
      }
      if (onChunk && requestBody.stream) {
        logToConsole("\u{1F504} Processing streaming response...", "debug");
        const reader = response.body?.getReader();
        const decoder = new TextDecoder();
        let fullResponse = "";
        if (!reader) {
          throw new Error("Response body reader not available");
        }
        try {
          while (true) {
            const { done, value } = await reader.read();
            if (done)
              break;
            const chunk = decoder.decode(value, { stream: true });
            const lines = chunk.split("\n");
            for (const line of lines) {
              if (line.startsWith("data: ")) {
                const data = line.slice(6);
                if (data === "[DONE]") {
                  logToConsole("\u2705 Streaming completed", "success");
                  return fullResponse;
                }
                try {
                  const parsed = JSON.parse(data);
                  if (parsed.choices && parsed.choices[0]?.delta?.content) {
                    const content = parsed.choices[0].delta.content;
                    fullResponse += content;
                    onChunk(content);
                    logToConsole(`\u{1F4DD} Streamed chunk: ${content.length} characters`, "debug");
                  }
                } catch (e) {
                  logToConsole(`\u26A0\uFE0F Ignoring malformed chunk: ${e}`, "debug");
                }
              }
            }
          }
          logToConsole(`\u2705 Streaming completed, total: ${fullResponse.length} characters`, "success");
          return fullResponse;
        } finally {
          reader.releaseLock();
        }
      } else {
        logToConsole("\u{1F4E5} Processing non-streaming response...", "debug");
        const data = await response.json();
        logToConsole(`\u{1F4CA} Response data keys: ${Object.keys(data).join(", ")}`, "debug");
        logToConsole(`\u{1F3AF} Choices count: ${data.choices?.length || 0}`, "debug");
        if (data.choices && data.choices.length > 0) {
          const content = data.choices[0]?.message?.content;
          if (content) {
            logToConsole(`\u2705 Successfully extracted response content (${content.length} characters)`, "success");
            logToConsole(`\u{1F4DD} Response preview: ${content.substring(0, 200)}${content.length > 200 ? "..." : ""}`, "debug");
            return content;
          } else {
            logToConsole("\u26A0\uFE0F Response content is empty or undefined", "warning");
            logToConsole(`\u{1F50D} Full response structure: ${JSON.stringify(data, null, 2)}`, "debug");
            return null;
          }
        } else {
          logToConsole("\u26A0\uFE0F No choices found in response", "warning");
          logToConsole(`\u{1F50D} Full response structure: ${JSON.stringify(data, null, 2)}`, "debug");
          return null;
        }
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error);
      const errorStack = error instanceof Error ? error.stack : "No stack trace available";
      logToConsole(`\u274C Groq API call failed: ${errorMessage}`, "error");
      logToConsole(`\u{1F50D} Error stack trace: ${errorStack}`, "debug");
      if (error instanceof TypeError && error.message.includes("fetch")) {
        logToConsole("\u{1F310} Network error detected - check internet connection", "error");
      } else if (error instanceof SyntaxError) {
        logToConsole("\u{1F4DD} JSON parsing error - invalid response format", "error");
      }
      return null;
    }
  }
  async function callOllamaAPI(prompt2) {
    try {
      logToConsole("\u{1F504} Preparing Ollama API fallback request...", "debug");
      logToConsole(`\u{1F310} Ollama URL: ${OLLAMA_URL}/api/generate`, "debug");
      logToConsole(`\u{1F916} Using model: ${OLLAMA_MODEL}`, "debug");
      logToConsole(`\u{1F4DD} Prompt length: ${prompt2.length} characters`, "debug");
      const requestBody = {
        model: OLLAMA_MODEL,
        prompt: prompt2,
        stream: false
      };
      logToConsole("\u{1F4E4} Sending request to Ollama API...", "debug");
      logToConsole(`\u{1F4CA} Request payload size: ${JSON.stringify(requestBody).length} characters`, "debug");
      const startTime = Date.now();
      const response = await fetch(`${OLLAMA_URL}/api/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(requestBody)
      });
      const endTime = Date.now();
      const responseTime = endTime - startTime;
      logToConsole(`\u23F1\uFE0F Ollama response received in ${responseTime}ms`, "debug");
      logToConsole(`\u{1F4E1} HTTP Status: ${response.status} ${response.statusText}`, "debug");
      logToConsole(`\u{1F4CB} Response headers: ${JSON.stringify(Object.fromEntries(response.headers.entries()))}`, "debug");
      if (!response.ok) {
        const errorText = await response.text();
        logToConsole(`\u274C Ollama API error response: ${errorText}`, "error");
        throw new Error(`Ollama API error: ${response.status} ${response.statusText} - ${errorText}`);
      }
      logToConsole("\u{1F4E5} Parsing Ollama JSON response...", "debug");
      const data = await response.json();
      logToConsole(`\u{1F4CA} Ollama response data keys: ${Object.keys(data).join(", ")}`, "debug");
      if (data.response) {
        logToConsole(`\u2705 Successfully extracted Ollama response content (${data.response.length} characters)`, "success");
        logToConsole(`\u{1F4DD} Ollama response preview: ${data.response.substring(0, 200)}${data.response.length > 200 ? "..." : ""}`, "debug");
        return data.response;
      } else {
        logToConsole("\u26A0\uFE0F Ollama response content is empty or undefined", "warning");
        logToConsole(`\u{1F50D} Full Ollama response structure: ${JSON.stringify(data, null, 2)}`, "debug");
        return null;
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error);
      const errorStack = error instanceof Error ? error.stack : "No stack trace available";
      logToConsole(`\u274C Ollama API call failed: ${errorMessage}`, "error");
      logToConsole(`\u{1F50D} Ollama error stack trace: ${errorStack}`, "debug");
      if (error instanceof TypeError && error.message.includes("fetch")) {
        logToConsole("\u{1F310} Ollama network error detected - check if Ollama is running locally", "error");
      } else if (error instanceof SyntaxError) {
        logToConsole("\u{1F4DD} Ollama JSON parsing error - invalid response format", "error");
      }
      return null;
    }
  }
  async function getGroqApiKey() {
    return new Promise((resolve) => {
      chrome.storage.sync.get(["groq_api_key"], (result) => {
        const apiKey = result.groq_api_key || null;
        if (apiKey) {
          logToConsole(`\u{1F511} API key found (${apiKey.substring(0, 8)}...)`, "debug");
        } else {
          logToConsole("\u274C No API key found in storage", "debug");
        }
        resolve(apiKey);
      });
    });
  }
  function handleStopGeneration() {
    if (abortController) {
      logToConsole("\u23F9\uFE0F Stopping generation...", "warning");
      abortController.abort();
      isGenerating = false;
      abortController = null;
      const stopGenerationBtn = document.getElementById("stop-generation");
      const realtimeResponse = document.getElementById("realtime-response");
      if (stopGenerationBtn) {
        stopGenerationBtn.style.display = "none";
      }
      if (realtimeResponse) {
        realtimeResponse.classList.remove("typing");
      }
      logToConsole("\u2705 Generation stopped", "info");
      showNotification("Generation stopped");
    }
  }
  async function handleCopyRealtime() {
    const realtimeResponse = document.getElementById("realtime-response");
    if (!realtimeResponse || !realtimeResponse.textContent) {
      logToConsole("\u274C No real-time content to copy", "error");
      showNotification("No content to copy!", true);
      return;
    }
    try {
      await navigator.clipboard.writeText(realtimeResponse.textContent);
      logToConsole("\u2705 Real-time response copied to clipboard", "success");
      showNotification("Real-time response copied!");
    } catch (error) {
      logToConsole(`\u274C Failed to copy real-time response: ${error}`, "error");
      showNotification("Failed to copy real-time response", true);
    }
  }
})();
