import { LinearClient } from './client';
export class LinearIntegrationService {
    constructor(config, dataManager) {
        this.config = config;
        this.client = new LinearClient(config.apiKey);
        this.dataManager = dataManager;
    }
    getSectionMappings() {
        return [
            {
                sectionName: 'position_details',
                taskTitle: 'Position Details',
                taskDescription: 'Job position information and requirements',
                priority: 1,
                labels: ['position', 'details']
            },
            {
                sectionName: 'job_requirements',
                taskTitle: 'Job Requirements',
                taskDescription: 'Required skills, experience, and qualifications',
                priority: 2,
                labels: ['requirements', 'skills']
            },
            {
                sectionName: 'company_information',
                taskTitle: 'Company Research',
                taskDescription: 'Company background, culture, and market position',
                priority: 3,
                labels: ['company', 'research']
            },
            {
                sectionName: 'skills_matrix',
                taskTitle: 'Skills Assessment',
                taskDescription: 'Skills gap analysis and development priorities',
                priority: 4,
                labels: ['skills', 'assessment']
            },
            {
                sectionName: 'application_materials',
                taskTitle: 'Application Materials',
                taskDescription: 'Resume, cover letter, and supporting documents',
                priority: 5,
                labels: ['materials', 'documents']
            },
            {
                sectionName: 'interview_schedule',
                taskTitle: 'Interview Schedule',
                taskDescription: 'Interview appointments and logistics',
                priority: 6,
                labels: ['interview', 'schedule']
            },
            {
                sectionName: 'interview_preparation',
                taskTitle: 'Interview Preparation',
                taskDescription: 'Preparation checklist and research',
                priority: 7,
                labels: ['interview', 'preparation']
            },
            {
                sectionName: 'communication_log',
                taskTitle: 'Communication Log',
                taskDescription: 'All communications with the company',
                priority: 8,
                labels: ['communication', 'log']
            },
            {
                sectionName: 'key_contacts',
                taskTitle: 'Key Contacts',
                taskDescription: 'Important contact information',
                priority: 9,
                labels: ['contacts', 'networking']
            },
            {
                sectionName: 'interview_feedback',
                taskTitle: 'Interview Feedback',
                taskDescription: 'Interview performance and feedback',
                priority: 10,
                labels: ['interview', 'feedback']
            },
            {
                sectionName: 'offer_details',
                taskTitle: 'Offer Details',
                taskDescription: 'Job offer information and negotiation',
                priority: 11,
                labels: ['offer', 'negotiation']
            },
            {
                sectionName: 'rejection_analysis',
                taskTitle: 'Rejection Analysis',
                taskDescription: 'Rejection reasons and lessons learned',
                priority: 12,
                labels: ['rejection', 'analysis']
            },
            {
                sectionName: 'privacy_policy',
                taskTitle: 'Privacy Policy',
                taskDescription: 'Privacy and consent tracking',
                priority: 13,
                labels: ['privacy', 'compliance']
            },
            {
                sectionName: 'lessons_learned',
                taskTitle: 'Lessons Learned',
                taskDescription: 'Insights and improvement strategies',
                priority: 14,
                labels: ['lessons', 'improvement']
            },
            {
                sectionName: 'performance_metrics',
                taskTitle: 'Performance Metrics',
                taskDescription: 'Application success metrics and tracking',
                priority: 15,
                labels: ['metrics', 'performance']
            },
            {
                sectionName: 'advisor_review',
                taskTitle: 'Advisor Review',
                taskDescription: 'Professional advisor feedback and recommendations',
                priority: 16,
                labels: ['advisor', 'review']
            }
        ];
    }
    formatSectionContent(sectionData, sectionName) {
        if (!sectionData || sectionData.length === 0) {
            return `No data available for ${sectionName.replace('_', ' ')}`;
        }
        const data = Array.isArray(sectionData) ? sectionData[0] : sectionData;
        let content = '';
        for (const [key, value] of Object.entries(data)) {
            if (key === 'id' || key === 'job_application_id' || key === 'created_at' || key === 'updated_at') {
                continue;
            }
            if (value !== null && value !== undefined && value !== '') {
                const formattedKey = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                const formattedValue = Array.isArray(value) ? value.join(', ') : String(value);
                content += `**${formattedKey}:** ${formattedValue}\n\n`;
            }
        }
        return content || `No detailed data available for ${sectionName.replace('_', ' ')}`;
    }
    async getLabelIds(labels, teamId) {
        try {
            const availableLabels = await this.client.getLabels(teamId);
            const labelIds = [];
            for (const labelName of labels) {
                const label = availableLabels.find(l => l.name.toLowerCase() === labelName.toLowerCase());
                if (label) {
                    labelIds.push(label.id);
                }
            }
            return labelIds;
        }
        catch (error) {
            console.warn('Failed to fetch labels, proceeding without labels:', error);
            return [];
        }
    }
    async exportJobToLinear(jobApplicationId) {
        try {
            // Get complete job application data
            const jobData = await this.dataManager.exportCurrentJobApplication();
            if (!jobData.jobApplication) {
                throw new Error('Job application not found');
            }
            const job = jobData.jobApplication;
            const sectionMappings = this.getSectionMappings();
            // Create main task
            const mainTaskTitle = `Job Application: ${job.job_title} at ${job.company_name}`;
            const mainTaskDescription = `
# Job Application Tracking

**Position:** ${job.job_title}
**Company:** ${job.company_name}
**Application Date:** ${job.application_date}
**Status:** ${job.status}
**URL:** ${job.canonical_url}

## Overview
This task tracks the complete application process for the ${job.job_title} position at ${job.company_name}.

## Sections
${sectionMappings.map(mapping => `- ${mapping.taskTitle}`).join('\n')}

---
*Created by JobOps Clipper Extension*
      `.trim();
            const mainTask = {
                title: mainTaskTitle,
                description: mainTaskDescription,
                teamId: this.config.teamId,
                projectId: this.config.projectId,
                priority: this.config.defaultPriority,
                assigneeId: this.config.assigneeId,
                labels: await this.getLabelIds(['job-application', 'tracking'], this.config.teamId)
            };
            const mainTaskIssue = await this.client.createIssue(mainTask);
            // Create subtasks for each section
            const subtasks = [];
            if (this.config.autoCreateSubtasks) {
                for (const mapping of sectionMappings) {
                    const sectionData = jobData[mapping.sectionName];
                    const sectionContent = this.formatSectionContent(sectionData, mapping.sectionName);
                    const subtask = {
                        title: mapping.taskTitle,
                        description: `
# ${mapping.taskTitle}

${mapping.taskDescription}

## Content
${sectionContent}

---
*Section from JobOps Clipper*
            `.trim(),
                        parentId: mainTaskIssue.id,
                        priority: mapping.priority,
                        labels: await this.getLabelIds(mapping.labels, this.config.teamId)
                    };
                    try {
                        const subtaskIssue = await this.client.createSubtask(subtask);
                        subtasks.push(subtaskIssue);
                    }
                    catch (error) {
                        console.error(`Failed to create subtask for ${mapping.sectionName}:`, error);
                    }
                }
            }
            return {
                mainTask: mainTaskIssue,
                subtasks,
                success: true
            };
        }
        catch (error) {
            console.error('Failed to export job to Linear:', error);
            return {
                mainTask: null,
                subtasks: [],
                success: false,
                error: error instanceof Error ? error.message : 'Unknown error'
            };
        }
    }
    async testConnection() {
        return await this.client.testConnection();
    }
    async getTeams() {
        return await this.client.getTeams();
    }
    async getProjects(teamId) {
        return await this.client.getProjects(teamId);
    }
    async getLabels(teamId) {
        return await this.client.getLabels(teamId);
    }
}
