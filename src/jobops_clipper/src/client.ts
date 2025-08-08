import { LinearTask, LinearSubtask, LinearIntegration } from './models';

export interface LinearUser {
  id: string;
  name: string;
  email: string;
}

export interface LinearTeam {
  id: string;
  name: string;
  key: string;
}

export interface LinearProject {
  id: string;
  name: string;
  description?: string;
}

export interface LinearLabel {
  id: string;
  name: string;
  color: string;
}

export interface LinearIssue {
  id: string;
  title: string;
  description: string;
  url: string;
  team: LinearTeam;
  project?: LinearProject;
  labels: LinearLabel[];
  assignee?: LinearUser;
  priority: number;
  createdAt: string;
  updatedAt: string;
}

export class LinearClient {
  private apiKey: string;
  private baseUrl = 'https://api.linear.app/graphql';

  constructor(apiKey: string) {
    this.apiKey = apiKey;
  }

  private async makeGraphQLRequest<T>(query: string, variables?: any): Promise<T> {
    const maxRetries = 3;
    let attempt = 0;
    let lastError: any = null;

    while (attempt <= maxRetries) {
      try {
        const response = await fetch(this.baseUrl, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${this.apiKey}`,
          },
          body: JSON.stringify({ query, variables }),
        });

        if (!response.ok) {
          const status = response.status;
          const shouldRetry = status === 429 || (status >= 500 && status < 600);
          const errorText = await response.text().catch(() => '');
          if (shouldRetry && attempt < maxRetries) {
            const backoff = Math.min(1000 * Math.pow(2, attempt) + Math.random() * 200, 5000);
            await new Promise(r => setTimeout(r, backoff));
            attempt++;
            continue;
          }
          throw new Error(`Linear API error: ${status} ${response.statusText} ${errorText}`);
        }

        const result = await response.json();
        if (result.errors) {
          throw new Error(`GraphQL errors: ${JSON.stringify(result.errors)}`);
        }
        return result.data;
      } catch (err) {
        lastError = err;
        // Retry on network errors
        if (attempt < maxRetries) {
          const backoff = Math.min(1000 * Math.pow(2, attempt) + Math.random() * 200, 5000);
          await new Promise(r => setTimeout(r, backoff));
          attempt++;
          continue;
        }
        break;
      }
    }
    throw lastError instanceof Error ? lastError : new Error(String(lastError));
  }

  async getCurrentUser(): Promise<LinearUser> {
    const query = `
      query {
        viewer {
          id
          name
          email
        }
      }
    `;

    const data = await this.makeGraphQLRequest<{ viewer: LinearUser }>(query);
    return data.viewer;
  }

  async getTeams(): Promise<LinearTeam[]> {
    const query = `
      query {
        teams {
          nodes {
            id
            name
            key
          }
        }
      }
    `;

    const data = await this.makeGraphQLRequest<{ teams: { nodes: LinearTeam[] } }>(query);
    return data.teams.nodes;
  }

  async getProjects(teamId: string): Promise<LinearProject[]> {
    const query = `
      query($teamId: String!) {
        team(id: $teamId) {
          projects {
            nodes {
              id
              name
              description
            }
          }
        }
      }
    `;

    const data = await this.makeGraphQLRequest<{ team: { projects: { nodes: LinearProject[] } } }>(query, { teamId });
    return data.team.projects.nodes;
  }

  async getLabels(teamId: string): Promise<LinearLabel[]> {
    const query = `
      query($teamId: String!) {
        team(id: $teamId) {
          labels {
            nodes {
              id
              name
              color
            }
          }
        }
      }
    `;

    const data = await this.makeGraphQLRequest<{ team: { labels: { nodes: LinearLabel[] } } }>(query, { teamId });
    return data.team.labels.nodes;
  }

  async createIssue(task: LinearTask): Promise<LinearIssue> {
    const mutation = `
      mutation($input: IssueCreateInput!) {
        issueCreate(input: $input) {
          issue {
            id
            title
            description
            url
            team {
              id
              name
              key
            }
            project {
              id
              name
            }
            labels {
              id
              name
              color
            }
            assignee {
              id
              name
              email
            }
            priority
            createdAt
            updatedAt
          }
        }
      }
    `;

    const input = {
      title: task.title,
      description: task.description,
      teamId: task.teamId,
      projectId: task.projectId,
      priority: task.priority,
      labelIds: task.labels,
      assigneeId: task.assigneeId,
    };

    const data = await this.makeGraphQLRequest<{ issueCreate: { issue: LinearIssue } }>(mutation, { input });
    return data.issueCreate.issue;
  }

  async createSubtask(subtask: LinearSubtask): Promise<LinearIssue> {
    const mutation = `
      mutation($input: IssueCreateInput!) {
        issueCreate(input: $input) {
          issue {
            id
            title
            description
            url
            team {
              id
              name
              key
            }
            project {
              id
              name
            }
            labels {
              id
              name
              color
            }
            assignee {
              id
              name
              email
            }
            priority
            createdAt
            updatedAt
          }
        }
      }
    `;

    const input = {
      title: subtask.title,
      description: subtask.description,
      parentId: subtask.parentId,
      priority: subtask.priority,
      labelIds: subtask.labels,
    };

    const data = await this.makeGraphQLRequest<{ issueCreate: { issue: LinearIssue } }>(mutation, { input });
    return data.issueCreate.issue;
  }

  async testConnection(): Promise<boolean> {
    try {
      await this.getCurrentUser();
      return true;
    } catch (error) {
      console.error('Linear connection test failed:', error);
      return false;
    }
  }
} 