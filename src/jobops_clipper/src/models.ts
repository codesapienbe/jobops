// Enums for better type safety
export enum ApplicationStatus {
    DRAFT = 'draft',
    SUBMITTED = 'submitted',
    UNDER_REVIEW = 'under_review',
    INTERVIEW_SCHEDULED = 'interview_scheduled',
    INTERVIEW_COMPLETED = 'interview_completed',
    OFFER_RECEIVED = 'offer_received',
    OFFER_ACCEPTED = 'offer_accepted',
    REJECTED = 'rejected',
    WITHDRAWN = 'withdrawn',
    ON_HOLD = 'on_hold'
  }
  
  export enum EmploymentType {
    FULL_TIME = 'full_time',
    PART_TIME = 'part_time',
    CONTRACT = 'contract',
    FREELANCE = 'freelance',
    REMOTE = 'remote',
    HYBRID = 'hybrid'
  }
  
  export enum InterviewStage {
    PHONE_SCREEN = 'phone_screen',
    FIRST_ROUND = 'first_round',
    TECHNICAL = 'technical',
    PANEL = 'panel',
    FINAL_ROUND = 'final_round',
    CULTURAL_FIT = 'cultural_fit'
  }
  
  export enum InterviewFormat {
    IN_PERSON = 'in_person',
    VIDEO_CALL = 'video_call',
    PHONE_CALL = 'phone_call',
    HYBRID = 'hybrid'
  }
  
  export enum CommunicationType {
    EMAIL = 'email',
    PHONE_CALL = 'phone_call',
    LINKEDIN_MESSAGE = 'linkedin_message',
    INTERVIEW = 'interview',
    TEXT_MESSAGE = 'text_message',
    VIDEO_CALL = 'video_call'
  }
  
  export enum SkillMatchStatus {
    STRONG_MATCH = 'strong_match',
    PARTIAL_MATCH = 'partial_match',
    GAP_IDENTIFIED = 'gap_identified',
    LEARNING_REQUIRED = 'learning_required'
  }
  
  export enum Priority {
    LOW = 'low',
    MEDIUM = 'medium',
    HIGH = 'high',
    CRITICAL = 'critical'
  }
  
  // Core interfaces
  export interface PositionDetails {
    jobTitle: string;
    companyName: string;
    applicationDate: Date;
    sourcePlatform: string;
    jobPostingUrl?: string;
    applicationDeadline?: Date;
    location: string;
    employmentType: EmploymentType;
    salaryRange?: string;
    jobDescription?: string;
  }
  
  export interface JobRequirements {
    requiredSkills: string[];
    preferredSkills: string[];
    requiredExperience: string;
    educationRequirements: string[];
    technicalRequirements: string[];
    industryKnowledge: string[];
  }
  
  export interface CompanyInformation {
    website?: string;
    headquarters: string;
    companySize?: string;
    annualRevenue?: string;
    industry: string;
    companyType: 'public' | 'private' | 'nonprofit';
    ceoLeadership?: string;
    missionStatement?: string;
    coreValues?: string[];
    recentNews?: string[];
    socialMediaPresence?: Record<string, string>;
    employeeReviews?: string;
    mainCompetitors?: string[];
    marketPosition?: string;
    uniqueSellingPoints?: string[];
  }
  
  export interface SkillAssessment {
    skillCategory: string;
    requiredByJob: boolean;
    currentLevel: number; // 1-5 scale
    matchStatus: SkillMatchStatus;
    evidenceExamples: string[];
  }
  
  export interface SkillsMatrix {
    assessments: SkillAssessment[];
    identifiedGaps: string[];
    developmentPriority: Priority;
    learningResources: string[];
    improvementTimeline: string;
  }
  
  export interface ApplicationMaterials {
    resumeVersion: string;
    tailoringChanges: string[];
    keywordsAdded: string[];
    sectionsModified: string[];
    fileName: string;
    coverLetterVersion?: string;
    keyPointsEmphasized?: string[];
    companySpecificContent?: string[];
    callToAction?: string;
    portfolioItems?: string[];
    referencesProvided?: string[];
    additionalDocuments?: string[];
  }
  
  export interface InterviewSchedule {
    stage: InterviewStage;
    date?: Date;
    time?: string;
    duration?: number; // in minutes
    format: InterviewFormat;
    interviewers: string[];
    location?: string;
    platform?: string;
    notes?: string;
  }
  
  export interface InterviewPreparation {
    companyResearchCompleted: boolean;
    questionsForInterviewer: string[];
    starExamplesReady: string[];
    technicalSkillsReviewed: boolean;
    portfolioReady: boolean;
    attirePrepared: boolean;
    technologyTested: boolean;
    additionalNotes?: string;
  }
  
  export interface CommunicationLog {
    id: string;
    date: Date;
    type: CommunicationType;
    contactPerson: string;
    contentSummary: string;
    followupRequired: boolean;
    responseReceived: boolean;
    attachments?: string[];
  }
  
  export interface KeyContacts {
    recruiterName?: string;
    recruiterContact?: string;
    hiringManager?: string;
    hrContact?: string;
    employeeReferral?: string;
    additionalContacts?: Record<string, string>;
  }
  
  export interface InterviewFeedback {
    interviewStage: InterviewStage;
    date: Date;
    duration: number;
    selfAssessment: {
      technicalKnowledge: number; // 1-5
      communicationClarity: number; // 1-5
      culturalFit: number; // 1-5
      questionAnswering: number; // 1-5
      questionsAsked: number; // 1-5
      overallConfidence: number; // 1-5
    };
    interviewerFeedback: {
      strengthsHighlighted: string[];
      areasForImprovement: string[];
      specificComments: string[];
      nextStepsMentioned: string[];
    };
    personalReflection: {
      whatWentWell: string[];
      whatCouldBeImproved: string[];
      lessonsLearned: string[];
      actionItems: string[];
    };
  }
  
  export interface OfferDetails {
    positionTitle: string;
    salaryOffered: string;
    benefitsPackage: string[];
    startDate?: Date;
    decisionDeadline?: Date;
    negotiationItems?: string[];
    counteroffers?: string[];
    finalAgreement?: string;
  }
  
  export interface RejectionAnalysis {
    reasonForRejection?: string;
    feedbackReceived: string[];
    areasForImprovement: string[];
    skillsExperienceGaps: string[];
  }
  
  export interface PrivacyPolicy {
    privacyPolicyReviewed: boolean;
    dataRetentionPeriod?: string;
    dataUsageConsentGiven: boolean;
    rightToDataDeletionUnderstood: boolean;
    personalDataShared: string[];
    backgroundChecksConsented: boolean;
    referenceCheckAuthorization: boolean;
  }
  
  export interface LessonsLearned {
    keyInsights: string[];
    skillsToDevelop: string[];
    interviewTechniquesToImprove: string[];
    resumeAdjustmentsNeeded: string[];
    resumeImprovementPlan: {
      skillsToAddHighlight: string[];
      experienceToArticulate: string[];
      keywordsToInclude: string[];
      formatChanges: string[];
    };
    futureApplicationStrategy: {
      similarRolesToTarget: string[];
      companiesToResearch: string[];
      networkingOpportunities: string[];
      professionalDevelopmentPriorities: string[];
    };
  }
  
  export interface PerformanceMetrics {
    applicationToInterviewRate?: number;
    interviewToSecondRoundRate?: number;
    finalInterviewToOfferRate?: number;
    timeFromApplicationToResponse?: number; // in days
    skillsMatchPercentage?: number;
  }
  
  export interface AdvisorReview {
    advisorName: string;
    reviewDate: Date;
    observations: {
      applicationStrengths: string[];
      interviewPerformance: string[];
      skillsDevelopmentPriorities: string[];
      strategicRecommendations: string[];
    };
    actionPlan: {
      shortTermGoals: string[]; // 1-3 months
      mediumTermGoals: string[]; // 3-6 months
      longTermCareerStrategy: string[];
    };
  }
  
  // Main Job Application class
  export class JobApplication {
    public id: string;
    public status: ApplicationStatus;
    public createdAt: Date;
    public updatedAt: Date;
    public positionDetails: PositionDetails;
    public jobRequirements: JobRequirements;
    public companyInformation: CompanyInformation;
    public skillsMatrix: SkillsMatrix;
    public applicationMaterials: ApplicationMaterials;
    public interviewSchedules: InterviewSchedule[];
    public interviewPreparation: InterviewPreparation;
    public communicationLog: CommunicationLog[];
    public keyContacts: KeyContacts;
    public interviewFeedback: InterviewFeedback[];
    public offerDetails?: OfferDetails;
    public rejectionAnalysis?: RejectionAnalysis;
    public privacyPolicy: PrivacyPolicy;
    public lessonsLearned: LessonsLearned;
    public performanceMetrics: PerformanceMetrics;
    public advisorReview?: AdvisorReview;
  
    constructor(positionDetails: PositionDetails) {
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
    private generateId(): string {
      return `job_app_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }
  
    private initializeJobRequirements(): JobRequirements {
      return {
        requiredSkills: [],
        preferredSkills: [],
        requiredExperience: '',
        educationRequirements: [],
        technicalRequirements: [],
        industryKnowledge: []
      };
    }
  
    private initializeCompanyInformation(): CompanyInformation {
      return {
        headquarters: '',
        industry: '',
        companyType: 'private'
      };
    }
  
    private initializeSkillsMatrix(): SkillsMatrix {
      return {
        assessments: [],
        identifiedGaps: [],
        developmentPriority: Priority.MEDIUM,
        learningResources: [],
        improvementTimeline: ''
      };
    }
  
    private initializeApplicationMaterials(): ApplicationMaterials {
      return {
        resumeVersion: '',
        tailoringChanges: [],
        keywordsAdded: [],
        sectionsModified: [],
        fileName: ''
      };
    }
  
    private initializeInterviewPreparation(): InterviewPreparation {
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
  
    private initializePrivacyPolicy(): PrivacyPolicy {
      return {
        privacyPolicyReviewed: false,
        dataUsageConsentGiven: false,
        rightToDataDeletionUnderstood: false,
        personalDataShared: [],
        backgroundChecksConsented: false,
        referenceCheckAuthorization: false
      };
    }
  
    private initializeLessonsLearned(): LessonsLearned {
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
    public updateStatus(newStatus: ApplicationStatus): void {
      this.status = newStatus;
      this.updatedAt = new Date();
    }
  
    public addCommunication(communication: Omit<CommunicationLog, 'id'>): void {
      const newCommunication: CommunicationLog = {
        ...communication,
        id: `comm_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
      };
      this.communicationLog.push(newCommunication);
      this.updatedAt = new Date();
    }
  
    public addInterviewSchedule(schedule: InterviewSchedule): void {
      this.interviewSchedules.push(schedule);
      this.updateStatus(ApplicationStatus.INTERVIEW_SCHEDULED);
    }
  
    public addInterviewFeedback(feedback: InterviewFeedback): void {
      this.interviewFeedback.push(feedback);
      this.updateStatus(ApplicationStatus.INTERVIEW_COMPLETED);
    }
  
    public calculateSkillsMatchPercentage(): number {
      if (this.skillsMatrix.assessments.length === 0) return 0;
      
      const strongMatches = this.skillsMatrix.assessments.filter(
        assessment => assessment.matchStatus === SkillMatchStatus.STRONG_MATCH
      ).length;
      
      return Math.round((strongMatches / this.skillsMatrix.assessments.length) * 100);
    }
  
    public getApplicationDuration(): number {
      const now = new Date();
      const diffTime = Math.abs(now.getTime() - this.createdAt.getTime());
      return Math.ceil(diffTime / (1000 * 60 * 60 * 24)); // days
    }
  
    public getNextActions(): string[] {
      const actions: string[] = [];
      
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
    public toJSON(): string {
      return JSON.stringify(this, null, 2);
    }
  
    public exportSummary(): JobApplicationSummary {
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
  
  // Summary interface for dashboard/listing views
  export interface JobApplicationSummary {
    id: string;
    position: string;
    status: ApplicationStatus;
    applicationDate: Date;
    location: string;
    skillsMatchPercentage: number;
    interviewCount: number;
    lastActivity: Date;
    nextActions: string[];
  }
  
  // Collection manager for multiple applications
  export class JobApplicationManager {
    private applications: Map<string, JobApplication> = new Map();
  
    public addApplication(application: JobApplication): void {
      this.applications.set(application.id, application);
    }
  
    public getApplication(id: string): JobApplication | undefined {
      return this.applications.get(id);
    }
  
    public getAllApplications(): JobApplication[] {
      return Array.from(this.applications.values());
    }
  
    public getApplicationsByStatus(status: ApplicationStatus): JobApplication[] {
      return this.getAllApplications().filter(app => app.status === status);
    }
  
    public getApplicationSummaries(): JobApplicationSummary[] {
      return this.getAllApplications().map(app => app.exportSummary());
    }
  
    public calculateOverallMetrics(): {
      totalApplications: number;
      interviewRate: number;
      offerRate: number;
      averageSkillsMatch: number;
    } {
      const applications = this.getAllApplications();
      const totalApplications = applications.length;
      
      if (totalApplications === 0) {
        return { totalApplications: 0, interviewRate: 0, offerRate: 0, averageSkillsMatch: 0 };
      }
  
      const interviewCount = applications.filter(app => 
        app.interviewFeedback.length > 0
      ).length;
      
      const offerCount = applications.filter(app => 
        app.status === ApplicationStatus.OFFER_RECEIVED || 
        app.status === ApplicationStatus.OFFER_ACCEPTED
      ).length;
  
      const skillsMatchTotal = applications.reduce((sum, app) => 
        sum + app.calculateSkillsMatchPercentage(), 0
      );
  
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
  
export interface LinearIntegration {
  apiKey?: string;
  teamId?: string;
  projectId?: string;
  enabled: boolean;
}

export interface LinearTask {
  title: string;
  description: string;
  teamId: string;
  projectId?: string;
  priority: number;
  labels?: string[];
  assigneeId?: string;
}

export interface LinearSubtask {
  title: string;
  description: string;
  parentId: string;
  priority: number;
  labels?: string[];
}

export interface LinearSectionMapping {
  sectionName: string;
  taskTitle: string;
  taskDescription: string;
  priority: number;
  labels: string[];
}
  