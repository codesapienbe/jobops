// Enums for better type safety
export var ApplicationStatus;
(function (ApplicationStatus) {
    ApplicationStatus["DRAFT"] = "draft";
    ApplicationStatus["SUBMITTED"] = "submitted";
    ApplicationStatus["UNDER_REVIEW"] = "under_review";
    ApplicationStatus["INTERVIEW_SCHEDULED"] = "interview_scheduled";
    ApplicationStatus["INTERVIEW_COMPLETED"] = "interview_completed";
    ApplicationStatus["OFFER_RECEIVED"] = "offer_received";
    ApplicationStatus["OFFER_ACCEPTED"] = "offer_accepted";
    ApplicationStatus["REJECTED"] = "rejected";
    ApplicationStatus["WITHDRAWN"] = "withdrawn";
    ApplicationStatus["ON_HOLD"] = "on_hold";
})(ApplicationStatus || (ApplicationStatus = {}));
export var EmploymentType;
(function (EmploymentType) {
    EmploymentType["FULL_TIME"] = "full_time";
    EmploymentType["PART_TIME"] = "part_time";
    EmploymentType["CONTRACT"] = "contract";
    EmploymentType["FREELANCE"] = "freelance";
    EmploymentType["REMOTE"] = "remote";
    EmploymentType["HYBRID"] = "hybrid";
})(EmploymentType || (EmploymentType = {}));
export var InterviewStage;
(function (InterviewStage) {
    InterviewStage["PHONE_SCREEN"] = "phone_screen";
    InterviewStage["FIRST_ROUND"] = "first_round";
    InterviewStage["TECHNICAL"] = "technical";
    InterviewStage["PANEL"] = "panel";
    InterviewStage["FINAL_ROUND"] = "final_round";
    InterviewStage["CULTURAL_FIT"] = "cultural_fit";
})(InterviewStage || (InterviewStage = {}));
export var InterviewFormat;
(function (InterviewFormat) {
    InterviewFormat["IN_PERSON"] = "in_person";
    InterviewFormat["VIDEO_CALL"] = "video_call";
    InterviewFormat["PHONE_CALL"] = "phone_call";
    InterviewFormat["HYBRID"] = "hybrid";
})(InterviewFormat || (InterviewFormat = {}));
export var CommunicationType;
(function (CommunicationType) {
    CommunicationType["EMAIL"] = "email";
    CommunicationType["PHONE_CALL"] = "phone_call";
    CommunicationType["LINKEDIN_MESSAGE"] = "linkedin_message";
    CommunicationType["INTERVIEW"] = "interview";
    CommunicationType["TEXT_MESSAGE"] = "text_message";
    CommunicationType["VIDEO_CALL"] = "video_call";
})(CommunicationType || (CommunicationType = {}));
export var SkillMatchStatus;
(function (SkillMatchStatus) {
    SkillMatchStatus["STRONG_MATCH"] = "strong_match";
    SkillMatchStatus["PARTIAL_MATCH"] = "partial_match";
    SkillMatchStatus["GAP_IDENTIFIED"] = "gap_identified";
    SkillMatchStatus["LEARNING_REQUIRED"] = "learning_required";
})(SkillMatchStatus || (SkillMatchStatus = {}));
export var Priority;
(function (Priority) {
    Priority["LOW"] = "low";
    Priority["MEDIUM"] = "medium";
    Priority["HIGH"] = "high";
    Priority["CRITICAL"] = "critical";
})(Priority || (Priority = {}));
// Main Job Application class
export class JobApplication {
    constructor(positionDetails) {
        this.id = this.generateId();
        this.status = ApplicationStatus.DRAFT;
        this.createdAt = new Date();
        this.updatedAt = new Date();
        this.positionDetails = positionDetails;
        // Initialize with default values
        this.jobRequirements = this.initializeJobRequirements();
        this.companyInformation = this.initializeCompanyInformation();
        this.skillsMatrix = this.initializeSkillsMatrix();
        this.applicationMaterials = this.initializeApplicationMaterials();
        this.interviewSchedules = [];
        this.interviewPreparation = this.initializeInterviewPreparation();
        this.communicationLog = [];
        this.keyContacts = {};
        this.interviewFeedback = [];
        this.privacyPolicy = this.initializePrivacyPolicy();
        this.lessonsLearned = this.initializeLessonsLearned();
        this.performanceMetrics = {};
    }
    // Utility methods
    generateId() {
        return `job_app_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }
    initializeJobRequirements() {
        return {
            requiredSkills: [],
            preferredSkills: [],
            requiredExperience: '',
            educationRequirements: [],
            technicalRequirements: [],
            industryKnowledge: []
        };
    }
    initializeCompanyInformation() {
        return {
            headquarters: '',
            industry: '',
            companyType: 'private'
        };
    }
    initializeSkillsMatrix() {
        return {
            assessments: [],
            identifiedGaps: [],
            developmentPriority: Priority.MEDIUM,
            learningResources: [],
            improvementTimeline: ''
        };
    }
    initializeApplicationMaterials() {
        return {
            resumeVersion: '',
            tailoringChanges: [],
            keywordsAdded: [],
            sectionsModified: [],
            fileName: ''
        };
    }
    initializeInterviewPreparation() {
        return {
            companyResearchCompleted: false,
            questionsForInterviewer: [],
            starExamplesReady: [],
            technicalSkillsReviewed: false,
            portfolioReady: false,
            attirePrepared: false,
            technologyTested: false
        };
    }
    initializePrivacyPolicy() {
        return {
            privacyPolicyReviewed: false,
            dataUsageConsentGiven: false,
            rightToDataDeletionUnderstood: false,
            personalDataShared: [],
            backgroundChecksConsented: false,
            referenceCheckAuthorization: false
        };
    }
    initializeLessonsLearned() {
        return {
            keyInsights: [],
            skillsToDevelop: [],
            interviewTechniquesToImprove: [],
            resumeAdjustmentsNeeded: [],
            resumeImprovementPlan: {
                skillsToAddHighlight: [],
                experienceToArticulate: [],
                keywordsToInclude: [],
                formatChanges: []
            },
            futureApplicationStrategy: {
                similarRolesToTarget: [],
                companiesToResearch: [],
                networkingOpportunities: [],
                professionalDevelopmentPriorities: []
            }
        };
    }
    // Business methods
    updateStatus(newStatus) {
        this.status = newStatus;
        this.updatedAt = new Date();
    }
    addCommunication(communication) {
        const newCommunication = {
            ...communication,
            id: `comm_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
        };
        this.communicationLog.push(newCommunication);
        this.updatedAt = new Date();
    }
    addInterviewSchedule(schedule) {
        this.interviewSchedules.push(schedule);
        this.updateStatus(ApplicationStatus.INTERVIEW_SCHEDULED);
    }
    addInterviewFeedback(feedback) {
        this.interviewFeedback.push(feedback);
        this.updateStatus(ApplicationStatus.INTERVIEW_COMPLETED);
    }
    calculateSkillsMatchPercentage() {
        if (this.skillsMatrix.assessments.length === 0)
            return 0;
        const strongMatches = this.skillsMatrix.assessments.filter(assessment => assessment.matchStatus === SkillMatchStatus.STRONG_MATCH).length;
        return Math.round((strongMatches / this.skillsMatrix.assessments.length) * 100);
    }
    getApplicationDuration() {
        const now = new Date();
        const diffTime = Math.abs(now.getTime() - this.createdAt.getTime());
        return Math.ceil(diffTime / (1000 * 60 * 60 * 24)); // days
    }
    getNextActions() {
        const actions = [];
        switch (this.status) {
            case ApplicationStatus.DRAFT:
                actions.push('Complete application materials');
                actions.push('Submit application');
                break;
            case ApplicationStatus.SUBMITTED:
                actions.push('Follow up if no response after 1 week');
                break;
            case ApplicationStatus.INTERVIEW_SCHEDULED:
                actions.push('Prepare for interview');
                actions.push('Research company further');
                break;
            case ApplicationStatus.INTERVIEW_COMPLETED:
                actions.push('Send thank you email');
                actions.push('Complete interview feedback');
                break;
            case ApplicationStatus.OFFER_RECEIVED:
                actions.push('Evaluate offer details');
                actions.push('Consider negotiation if needed');
                break;
        }
        return actions;
    }
    // Export methods for reporting
    toJSON() {
        return JSON.stringify(this, null, 2);
    }
    exportSummary() {
        return {
            id: this.id,
            position: `${this.positionDetails.jobTitle} at ${this.positionDetails.companyName}`,
            status: this.status,
            applicationDate: this.positionDetails.applicationDate,
            location: this.positionDetails.location,
            skillsMatchPercentage: this.calculateSkillsMatchPercentage(),
            interviewCount: this.interviewFeedback.length,
            lastActivity: this.updatedAt,
            nextActions: this.getNextActions()
        };
    }
}
// Collection manager for multiple applications
export class JobApplicationManager {
    constructor() {
        this.applications = new Map();
    }
    addApplication(application) {
        this.applications.set(application.id, application);
    }
    getApplication(id) {
        return this.applications.get(id);
    }
    getAllApplications() {
        return Array.from(this.applications.values());
    }
    getApplicationsByStatus(status) {
        return this.getAllApplications().filter(app => app.status === status);
    }
    getApplicationSummaries() {
        return this.getAllApplications().map(app => app.exportSummary());
    }
    calculateOverallMetrics() {
        const applications = this.getAllApplications();
        const totalApplications = applications.length;
        if (totalApplications === 0) {
            return { totalApplications: 0, interviewRate: 0, offerRate: 0, averageSkillsMatch: 0 };
        }
        const interviewCount = applications.filter(app => app.interviewFeedback.length > 0).length;
        const offerCount = applications.filter(app => app.status === ApplicationStatus.OFFER_RECEIVED ||
            app.status === ApplicationStatus.OFFER_ACCEPTED).length;
        const skillsMatchTotal = applications.reduce((sum, app) => sum + app.calculateSkillsMatchPercentage(), 0);
        return {
            totalApplications,
            interviewRate: Math.round((interviewCount / totalApplications) * 100),
            offerRate: Math.round((offerCount / totalApplications) * 100),
            averageSkillsMatch: Math.round(skillsMatchTotal / totalApplications)
        };
    }
}
// Export all types and classes
export default JobApplication;
