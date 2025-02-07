from typing import Any, Dict, Optional
from config import CONFIG
from smolagents import tool
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


@tool
def get_my_jira_issues() -> Dict[str, Any]:
    """Obtiene las tareas de Jira asignadas al usuario actual y devuelve los datos en JSON."""
    
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
                    "status": issue["fields"]["status"]["name"]
                }
                for issue in issues["issues"]
            ]
        }

    except Exception as e:
        return {"error": f"Error fetching Jira issues: {str(e)}"}