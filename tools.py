import json
from typing import Any, Dict, Optional
from config import CONFIG
from smolagents import tool, Tool
from atlassian import Jira


class JiraClient:
    def __init__(self):
        try:
            self.jira = Jira(
                url=CONFIG['JIRA_INSTANCE_URL'],
                username=CONFIG['JIRA_USERNAME'],
                password=CONFIG["JIRA_API_TOKEN"],
                cloud=CONFIG["JIRA_CLOUD"]
            )
        except Exception as e:
            print(f"Failed to initialize Jira client: {e}")
            self.jira = None

jira_client = JiraClient()  # Instancia global del cliente Jira


class JiraDataTool(Tool):
    name = "Jira issues data retriever"
    description = """
    This is a tool that makes a request to the jira API to get all the issues and returns only the jira issues
    that the user is asking for with the information needed.
    """
    inputs = {
        "status": {
            "type": "string",
            "description": "the status of the requested issues",
        }
    }
    
    output_type = "string"
    
    


@tool
def get_my_jira_issues() -> Dict[str, Any]:
    """Obtains the Jira issues assigned to the current user and returns them as JSON."""
    
    if not jira_client.jira:
        return {"error": "Jira client is not initialized. Check environment variables."}

    try:
        jql = "assignee = currentUser() ORDER BY created DESC"
        issues = jira_client.jira.jql(jql)

        if not issues.get("issues"):
            return {"message": "No issues found assigned to you."}

        return {
            "issues": [
                {
                    "key": issue["key"],
                    "summary": issue["fields"]["summary"],
                    "status": issue["fields"]["status"]["name"],
                }
                for issue in issues["issues"]
            ]
        }

    except Exception as e:
        return {"error": f"Error fetching Jira issues: {str(e)}"}
    

@tool
def get_finished_issues() -> Dict[str, Any]:
    """Obtains the Jira issues that are finished and returns them as JSON."""
    
    if not jira_client.jira:
        return {"error": "Jira client is not initialized. Check environment variables."}
    
    try:
        jql = "status = Done ORDER BY created DESC"
        issues = jira_client.jira.jql(jql)
        if not issues.get("issues"):
            return {"message": "No finished issues found."}
        
        
        return issues
    
    except Exception as e:
        return {"error": f"Error fetching Jira issues: {str(e)}"}
    


class createJiraIssueTool(Tool):
    name = "create_jira_issue"
    description = "Create new Jira issue with the fields defined by the inputs"
    inputs = {
        "project_id": {
            "type": "string",
            "description": "id of the project of the issue"
        },
        "summary": {
            "type": "string",
            "description": "title of the issue",
        },
        "description": {
            "type": "string",
            "description": "description of the issue"
        },
        "id_issuetype": {
            "type": "string",
            "description": "id of the issue type used"
        }
    }
    
    output_type = "string"
    
    def forward(self, project_id: str, summary: str, description: str, id_issuetype: str):
        if not jira_client.jira:
            return {"error": "Jira client is not initialized. Check environment variables."}

        try:
            issue_data = {
                "project": {"id": project_id},
                "summary": summary,
                "description": description,
                "issuetype": {"id": id_issuetype},
            }
            new_issue = jira_client.jira.create_issue(fields=issue_data)
            result = {
                "message": "Incidencia creada exitosamente.",
                "issue": new_issue,
            }
            
            return json.dumps(result)
            
        except Exception as e:
            return {"error": f"Error al crear la incidencia en Jira: {str(e)}"}