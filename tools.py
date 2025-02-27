import json
from typing import Any, Dict, Optional
from cache import get_cached_jira_issues
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

class getAllJiraIssuesTool(Tool):
    name = "get_all_jira_issues"
    description = "Return all the Jira issues of the site"
    inputs = {}
    output_type = "string"
    
    def forward(self): 
        issues = get_cached_jira_issues()
        print(issues)
        
        #return json.dumps(issues) if isinstance(issues, dict) else "No hay incidencias almacenadas."
        if not issues or not isinstance(issues, list):
            return "No hay incidencias almacenadas."

        return json.dumps(issues, indent=2)


class createJiraIssueTool(Tool):
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
            "description": "name of the issue type used"
        }
    }
    
    output_type = "string"
    
    def forward(self, project_key: str, summary: str, description: str, issuetype: str):
        if not jira_client.jira:
            return {"error": "Jira client is not initialized. Check environment variables."}

        try:
            issue_data = {
                "project": {"key": project_key},
                "summary": summary,
                "description": description,
                "issuetype": {"name": issuetype},
            }
            new_issue = jira_client.jira.create_issue(fields=issue_data)
            result = {
                "message": "Incidencia creada exitosamente.",
                "issue": new_issue,
            }
            
            return json.dumps(result)
            
        except Exception as e:
            return {"error": f"Error al crear la incidencia en Jira: {str(e)}"}