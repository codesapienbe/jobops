// Data Manager for JobOps Clipper
// Handles integration between UI forms and database
import { jobOpsDatabase } from './database';
export class JobOpsDataManager {
    constructor() {
        this.currentJobApplicationId = null;
        this.currentCanonicalUrl = null;
        this.initializeDataManager();
    }
    async initializeDataManager() {
        try {
            // Wait for database to be ready
            await new Promise(resolve => setTimeout(resolve, 100));
            console.log('JobOps Data Manager initialized');
        }
        catch (error) {
            console.error('Failed to initialize data manager:', error);
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
        }
        catch (error) {
            console.error('Error checking existing job:', error);
            return false;
        }
    }
    // Create new job application
    async createNewJobApplication(jobData) {
        try {
            const canonicalUrl = jobOpsDatabase.getCanonicalUrl(jobData.url || '');
            this.currentCanonicalUrl = canonicalUrl;
            const jobApplicationData = {
                canonical_url: canonicalUrl,
                job_title: jobData.title || '',
                company_name: jobData.company || '',
                application_date: new Date().toISOString(),
                status: 'draft'
            };
            this.currentJobApplicationId = await jobOpsDatabase.createJobApplication(jobApplicationData);
            console.log('New job application created:', this.currentJobApplicationId);
            return this.currentJobApplicationId;
        }
        catch (error) {
            console.error('Error creating new job application:', error);
            throw error;
        }
    }
    // Load all data for a job application
    async loadJobApplicationData(jobApplicationId) {
        try {
            const completeData = await jobOpsDatabase.getCompleteJobApplication(jobApplicationId);
            this.populateUIWithData(completeData);
        }
        catch (error) {
            console.error('Error loading job application data:', error);
        }
    }
    // Save position details
    async savePositionDetails(data) {
        if (!this.currentJobApplicationId) {
            throw new Error('No active job application');
        }
        try {
            const positionDetailsData = {
                job_application_id: this.currentJobApplicationId,
                job_title: data.jobTitle || '',
                company_name: data.companyName || '',
                application_date: data.applicationDate || new Date().toISOString(),
                source_platform: data.sourcePlatform || '',
                job_posting_url: data.jobPostingUrl || '',
                application_deadline: data.applicationDeadline || '',
                location: data.location || '',
                employment_type: data.employmentType || '',
                salary_range: data.salaryRange || '',
                job_description: data.jobDescription || ''
            };
            await jobOpsDatabase.saveSectionData('position_details', positionDetailsData);
            console.log('Position details saved');
        }
        catch (error) {
            console.error('Error saving position details:', error);
            throw error;
        }
    }
    // Save job requirements
    async saveJobRequirements(data) {
        if (!this.currentJobApplicationId) {
            throw new Error('No active job application');
        }
        try {
            const jobRequirementsData = {
                job_application_id: this.currentJobApplicationId,
                required_skills: JSON.stringify(data.requiredSkills || []),
                preferred_skills: JSON.stringify(data.preferredSkills || []),
                required_experience: data.requiredExperience || '',
                education_requirements: JSON.stringify(data.educationRequirements || []),
                technical_requirements: JSON.stringify(data.technicalRequirements || []),
                industry_knowledge: JSON.stringify(data.industryKnowledge || [])
            };
            await jobOpsDatabase.saveSectionData('job_requirements', jobRequirementsData);
            console.log('Job requirements saved');
        }
        catch (error) {
            console.error('Error saving job requirements:', error);
            throw error;
        }
    }
    // Save company information
    async saveCompanyInformation(data) {
        if (!this.currentJobApplicationId) {
            throw new Error('No active job application');
        }
        try {
            const companyInformationData = {
                job_application_id: this.currentJobApplicationId,
                website: data.website || '',
                headquarters: data.headquarters || '',
                company_size: data.companySize || '',
                annual_revenue: data.annualRevenue || '',
                industry: data.industry || '',
                company_type: data.companyType || '',
                ceo_leadership: data.ceoLeadership || '',
                mission_statement: data.missionStatement || '',
                core_values: JSON.stringify(data.coreValues || []),
                recent_news: JSON.stringify(data.recentNews || []),
                social_media_presence: JSON.stringify(data.socialMediaPresence || {}),
                employee_reviews: data.employeeReviews || '',
                main_competitors: JSON.stringify(data.mainCompetitors || []),
                market_position: data.marketPosition || '',
                unique_selling_points: JSON.stringify(data.uniqueSellingPoints || [])
            };
            await jobOpsDatabase.saveSectionData('company_information', companyInformationData);
            console.log('Company information saved');
        }
        catch (error) {
            console.error('Error saving company information:', error);
            throw error;
        }
    }
    // Save skills matrix
    async saveSkillsMatrix(data) {
        if (!this.currentJobApplicationId) {
            throw new Error('No active job application');
        }
        try {
            const skillsMatrixData = {
                job_application_id: this.currentJobApplicationId,
                identified_gaps: JSON.stringify(data.identifiedGaps || []),
                development_priority: data.developmentPriority || 'medium',
                learning_resources: JSON.stringify(data.learningResources || []),
                improvement_timeline: data.improvementTimeline || ''
            };
            const skillsMatrixId = await jobOpsDatabase.saveSectionData('skills_matrix', skillsMatrixData);
            // Save skill assessments
            if (data.assessments && Array.isArray(data.assessments)) {
                for (const assessment of data.assessments) {
                    const skillAssessmentData = {
                        skills_matrix_id: skillsMatrixId,
                        skill_category: assessment.skillCategory || '',
                        required_by_job: assessment.requiredByJob || false,
                        current_level: assessment.currentLevel || 1,
                        match_status: assessment.matchStatus || 'partial_match',
                        evidence_examples: JSON.stringify(assessment.evidenceExamples || [])
                    };
                    // Note: skill_assessments table uses skills_matrix_id instead of job_application_id
                    // This is a special case handled in the database layer
                    await jobOpsDatabase.saveSectionData('skill_assessments', skillAssessmentData);
                }
            }
            console.log('Skills matrix saved');
        }
        catch (error) {
            console.error('Error saving skills matrix:', error);
            throw error;
        }
    }
    // Save application materials
    async saveApplicationMaterials(data) {
        if (!this.currentJobApplicationId) {
            throw new Error('No active job application');
        }
        try {
            const applicationMaterialsData = {
                job_application_id: this.currentJobApplicationId,
                resume_version: data.resumeVersion || '',
                tailoring_changes: JSON.stringify(data.tailoringChanges || []),
                keywords_added: JSON.stringify(data.keywordsAdded || []),
                sections_modified: JSON.stringify(data.sectionsModified || []),
                file_name: data.fileName || '',
                cover_letter_version: data.coverLetterVersion || '',
                key_points_emphasized: JSON.stringify(data.keyPointsEmphasized || []),
                company_specific_content: JSON.stringify(data.companySpecificContent || []),
                call_to_action: data.callToAction || '',
                portfolio_items: JSON.stringify(data.portfolioItems || []),
                references_provided: JSON.stringify(data.referencesProvided || []),
                additional_documents: JSON.stringify(data.additionalDocuments || [])
            };
            await jobOpsDatabase.saveSectionData('application_materials', applicationMaterialsData);
            console.log('Application materials saved');
        }
        catch (error) {
            console.error('Error saving application materials:', error);
            throw error;
        }
    }
    // Save interview schedule
    async saveInterviewSchedule(data) {
        if (!this.currentJobApplicationId) {
            throw new Error('No active job application');
        }
        try {
            const interviewScheduleData = {
                job_application_id: this.currentJobApplicationId,
                stage: data.stage || '',
                date: data.date || '',
                time: data.time || '',
                duration: data.duration || 0,
                format: data.format || '',
                interviewers: JSON.stringify(data.interviewers || []),
                location: data.location || '',
                platform: data.platform || '',
                notes: data.notes || ''
            };
            await jobOpsDatabase.saveSectionData('interview_schedule', interviewScheduleData);
            console.log('Interview schedule saved');
        }
        catch (error) {
            console.error('Error saving interview schedule:', error);
            throw error;
        }
    }
    // Save interview preparation
    async saveInterviewPreparation(data) {
        if (!this.currentJobApplicationId) {
            throw new Error('No active job application');
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
                additional_notes: data.additionalNotes || ''
            };
            await jobOpsDatabase.saveSectionData('interview_preparation', interviewPreparationData);
            console.log('Interview preparation saved');
        }
        catch (error) {
            console.error('Error saving interview preparation:', error);
            throw error;
        }
    }
    // Save communication log
    async saveCommunicationLog(data) {
        if (!this.currentJobApplicationId) {
            throw new Error('No active job application');
        }
        try {
            const communicationLogData = {
                job_application_id: this.currentJobApplicationId,
                date: data.date || new Date().toISOString(),
                type: data.type || '',
                contact_person: data.contactPerson || '',
                content_summary: data.contentSummary || '',
                followup_required: data.followupRequired || false,
                response_received: data.responseReceived || false,
                attachments: JSON.stringify(data.attachments || [])
            };
            await jobOpsDatabase.saveSectionData('communication_log', communicationLogData);
            console.log('Communication log saved');
        }
        catch (error) {
            console.error('Error saving communication log:', error);
            throw error;
        }
    }
    // Save key contacts
    async saveKeyContacts(data) {
        if (!this.currentJobApplicationId) {
            throw new Error('No active job application');
        }
        try {
            const keyContactsData = {
                job_application_id: this.currentJobApplicationId,
                recruiter_name: data.recruiterName || '',
                recruiter_contact: data.recruiterContact || '',
                hiring_manager: data.hiringManager || '',
                hr_contact: data.hrContact || '',
                employee_referral: data.employeeReferral || '',
                additional_contacts: JSON.stringify(data.additionalContacts || {})
            };
            await jobOpsDatabase.saveSectionData('key_contacts', keyContactsData);
            console.log('Key contacts saved');
        }
        catch (error) {
            console.error('Error saving key contacts:', error);
            throw error;
        }
    }
    // Save interview feedback
    async saveInterviewFeedback(data) {
        if (!this.currentJobApplicationId) {
            throw new Error('No active job application');
        }
        try {
            const interviewFeedbackData = {
                job_application_id: this.currentJobApplicationId,
                interview_stage: data.interviewStage || '',
                date: data.date || new Date().toISOString(),
                duration: data.duration || 0,
                self_assessment: JSON.stringify(data.selfAssessment || {}),
                interviewer_feedback: JSON.stringify(data.interviewerFeedback || {}),
                personal_reflection: JSON.stringify(data.personalReflection || {})
            };
            await jobOpsDatabase.saveSectionData('interview_feedback', interviewFeedbackData);
            console.log('Interview feedback saved');
        }
        catch (error) {
            console.error('Error saving interview feedback:', error);
            throw error;
        }
    }
    // Save offer details
    async saveOfferDetails(data) {
        if (!this.currentJobApplicationId) {
            throw new Error('No active job application');
        }
        try {
            const offerDetailsData = {
                job_application_id: this.currentJobApplicationId,
                position_title: data.positionTitle || '',
                salary_offered: data.salaryOffered || '',
                benefits_package: JSON.stringify(data.benefitsPackage || []),
                start_date: data.startDate || '',
                decision_deadline: data.decisionDeadline || '',
                negotiation_items: JSON.stringify(data.negotiationItems || []),
                counteroffers: JSON.stringify(data.counteroffers || []),
                final_agreement: data.finalAgreement || ''
            };
            await jobOpsDatabase.saveSectionData('offer_details', offerDetailsData);
            console.log('Offer details saved');
        }
        catch (error) {
            console.error('Error saving offer details:', error);
            throw error;
        }
    }
    // Save rejection analysis
    async saveRejectionAnalysis(data) {
        if (!this.currentJobApplicationId) {
            throw new Error('No active job application');
        }
        try {
            const rejectionAnalysisData = {
                job_application_id: this.currentJobApplicationId,
                reason_for_rejection: data.reasonForRejection || '',
                feedback_received: JSON.stringify(data.feedbackReceived || []),
                areas_for_improvement: JSON.stringify(data.areasForImprovement || []),
                skills_experience_gaps: JSON.stringify(data.skillsExperienceGaps || [])
            };
            await jobOpsDatabase.saveSectionData('rejection_analysis', rejectionAnalysisData);
            console.log('Rejection analysis saved');
        }
        catch (error) {
            console.error('Error saving rejection analysis:', error);
            throw error;
        }
    }
    // Save privacy policy
    async savePrivacyPolicy(data) {
        if (!this.currentJobApplicationId) {
            throw new Error('No active job application');
        }
        try {
            const privacyPolicyData = {
                job_application_id: this.currentJobApplicationId,
                privacy_policy_reviewed: data.privacyPolicyReviewed || false,
                data_retention_period: data.dataRetentionPeriod || '',
                data_usage_consent_given: data.dataUsageConsentGiven || false,
                right_to_data_deletion_understood: data.rightToDataDeletionUnderstood || false,
                personal_data_shared: JSON.stringify(data.personalDataShared || []),
                background_checks_consented: data.backgroundChecksConsented || false,
                reference_check_authorization: data.referenceCheckAuthorization || false
            };
            await jobOpsDatabase.saveSectionData('privacy_policy', privacyPolicyData);
            console.log('Privacy policy saved');
        }
        catch (error) {
            console.error('Error saving privacy policy:', error);
            throw error;
        }
    }
    // Save lessons learned
    async saveLessonsLearned(data) {
        if (!this.currentJobApplicationId) {
            throw new Error('No active job application');
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
            await jobOpsDatabase.saveSectionData('lessons_learned', lessonsLearnedData);
            console.log('Lessons learned saved');
        }
        catch (error) {
            console.error('Error saving lessons learned:', error);
            throw error;
        }
    }
    // Save performance metrics
    async savePerformanceMetrics(data) {
        if (!this.currentJobApplicationId) {
            throw new Error('No active job application');
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
            await jobOpsDatabase.saveSectionData('performance_metrics', performanceMetricsData);
            console.log('Performance metrics saved');
        }
        catch (error) {
            console.error('Error saving performance metrics:', error);
            throw error;
        }
    }
    // Save advisor review
    async saveAdvisorReview(data) {
        if (!this.currentJobApplicationId) {
            throw new Error('No active job application');
        }
        try {
            const advisorReviewData = {
                job_application_id: this.currentJobApplicationId,
                advisor_name: data.advisorName || '',
                review_date: data.reviewDate || new Date().toISOString(),
                observations: JSON.stringify(data.observations || {}),
                action_plan: JSON.stringify(data.actionPlan || {})
            };
            await jobOpsDatabase.saveSectionData('advisor_review', advisorReviewData);
            console.log('Advisor review saved');
        }
        catch (error) {
            console.error('Error saving advisor review:', error);
            throw error;
        }
    }
    // Update job application status
    async updateJobStatus(status) {
        if (!this.currentJobApplicationId) {
            throw new Error('No active job application');
        }
        try {
            await jobOpsDatabase.updateJobApplication(this.currentJobApplicationId, { status });
            console.log('Job status updated to:', status);
        }
        catch (error) {
            console.error('Error updating job status:', error);
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
        // This method will be implemented to populate the UI forms with loaded data
        // For now, it's a placeholder that will be expanded as we implement the form fields
        console.log('Populating UI with loaded data:', data);
        // TODO: Implement form population logic for each section
        // This will be done as we implement the individual form fields
    }
    // Export current job application data
    async exportCurrentJobApplication() {
        if (!this.currentJobApplicationId) {
            throw new Error('No active job application');
        }
        try {
            return await jobOpsDatabase.getCompleteJobApplication(this.currentJobApplicationId);
        }
        catch (error) {
            console.error('Error exporting job application:', error);
            throw error;
        }
    }
    // Delete current job application
    async deleteCurrentJobApplication() {
        if (!this.currentJobApplicationId) {
            throw new Error('No active job application');
        }
        try {
            await jobOpsDatabase.deleteJobApplication(this.currentJobApplicationId);
            this.currentJobApplicationId = null;
            this.currentCanonicalUrl = null;
            console.log('Job application deleted');
        }
        catch (error) {
            console.error('Error deleting job application:', error);
            throw error;
        }
    }
    // Get all job applications for dashboard
    async getAllJobApplications() {
        try {
            return await jobOpsDatabase.getAllJobApplications();
        }
        catch (error) {
            console.error('Error getting all job applications:', error);
            throw error;
        }
    }
    // Export entire database
    async exportDatabase() {
        try {
            return await jobOpsDatabase.exportDatabase();
        }
        catch (error) {
            console.error('Error exporting database:', error);
            throw error;
        }
    }
    // Import database
    async importDatabase(data) {
        try {
            await jobOpsDatabase.importDatabase(data);
            console.log('Database imported successfully');
        }
        catch (error) {
            console.error('Error importing database:', error);
            throw error;
        }
    }
}
// Export singleton instance
export const jobOpsDataManager = new JobOpsDataManager();
