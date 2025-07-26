export class LinearClient {
    constructor(apiKey) {
        this.baseUrl = 'https://api.linear.app/graphql';
        this.apiKey = apiKey;
    }
    async makeGraphQLRequest(query, variables) {
        const response = await fetch(this.baseUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${this.apiKey}`,
            },
            body: JSON.stringify({
                query,
                variables,
            }),
        });
        if (!response.ok) {
            throw new Error(`Linear API error: ${response.status} ${response.statusText}`);
        }
        const result = await response.json();
        if (result.errors) {
            throw new Error(`GraphQL errors: ${JSON.stringify(result.errors)}`);
        }
        return result.data;
    }
    async getCurrentUser() {
        const query = `
      query {
        viewer {
          id
          name
          email
        }
      }
    `;
        const data = await this.makeGraphQLRequest(query);
        return data.viewer;
    }
    async getTeams() {
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
        const data = await this.makeGraphQLRequest(query);
        return data.teams.nodes;
    }
    async getProjects(teamId) {
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
        const data = await this.makeGraphQLRequest(query, { teamId });
        return data.team.projects.nodes;
    }
    async getLabels(teamId) {
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
        const data = await this.makeGraphQLRequest(query, { teamId });
        return data.team.labels.nodes;
    }
    async createIssue(task) {
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
        const data = await this.makeGraphQLRequest(mutation, { input });
        return data.issueCreate.issue;
    }
    async createSubtask(subtask) {
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
        const data = await this.makeGraphQLRequest(mutation, { input });
        return data.issueCreate.issue;
    }
    async testConnection() {
        try {
            await this.getCurrentUser();
            return true;
        }
        catch (error) {
            console.error('Linear connection test failed:', error);
            return false;
        }
    }
}
