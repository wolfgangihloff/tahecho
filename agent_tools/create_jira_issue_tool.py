import json
from smolagents import Tool

from jira_integration.jira_client import jira_client


class CreateJiraIssueTool(Tool):
    name = "create_jira_issue"
    description = "Create new Jira issue with the fields defined by the inputs"
    inputs = {
        "project_key": {
            "type": "string",
            "description": "key of the project of the issue"
        },
        "summary": {
            "type": "string",
            "description": "title of the issue",
        },
        "description": {
            "type": "string",
            "description": "description of the issue"
        },
        "issuetype": {
            "type": "string",
            "description": "id of the issue type used"
        }
    }
    
    output_type = "string"
    
    def forward(self, project_key: str, summary: str, description: str, issuetype: str):
        if not jira_client.get_instance():
            return {"error": "Jira client is not initialized. Check environment variables."}

        try:
            issue_data = {
                "project": {"key": project_key},
                "summary": summary,
                "description": description,
                "issuetype": {"name": issuetype},
            }
            new_issue = jira_client.get_instance().create_issue(fields=issue_data)
            result = {
                "message": "Incidencia creada exitosamente.",
                "issue": f"{jira_client.get_instance().url}/jira/software/projects/{project_key}/list?selectedIssue={new_issue['key']}",
            }
            
            return json.dumps(result)
            
        except Exception as e:
            return {"error": f"Error al crear la incidencia en Jira: {str(e)}"}
        
        
