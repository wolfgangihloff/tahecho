from atlassian import Jira
from config import CONFIG

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

def get_all_jira_issues():
    """Obtiene todas las issues de Jira."""
    try:
        jql = "ORDER BY created DESC"
        issues = jira_client.jql(jql)

        if not issues.get('issues'):
            return {"message": "No se encontraron incidencias en Jira."}


        filtered_issues = []
        for issue in issues["issues"]:
            filtered_issue = {
                "id": issue.get("id"),
                "key": issue.get("key"),
                "self": issue.get("self"),
                "summary": issue["fields"].get("summary"),
                "description": issue["fields"].get("description"),
                "status": {
                    "name": issue["fields"]["status"].get("name"),
                    "statusCategory": {
                        "name": issue["fields"]["status"]["statusCategory"].get("name")
                    }
                } if "status" in issue["fields"] else None,
                "priority": {
                    "name": issue["fields"]["priority"].get("name")
                } if "priority" in issue["fields"] else None,
                "issuetype": {
                    "name": issue["fields"]["issuetype"].get("name"),
                    "description": issue["fields"]["issuetype"].get("description")
                } if "issuetype" in issue["fields"] else None,
                "project": {
                    "key": issue["fields"]["project"].get("key"),
                    "name": issue["fields"]["project"].get("name")
                } if "project" in issue["fields"] else None,
                "assignee": issue["fields"].get("assignee"),
                "reporter": {
                    "displayName": issue["fields"]["reporter"].get("displayName"),
                    "emailAddress": issue["fields"]["reporter"].get("emailAddress")
                } if "reporter" in issue["fields"] else None,
                "created": issue["fields"].get("created"),
                "updated": issue["fields"].get("updated"),
                "resolution": issue["fields"].get("resolution"),
                "resolutiondate": issue["fields"].get("resolutiondate"),
                "duedate": issue["fields"].get("duedate"),
                "labels": issue["fields"].get("labels", []),
            }
            filtered_issues.append(filtered_issue)

        return filtered_issues
    except Exception as e:
        return {"error": f"Error al obtener las incidencias de Jira: {str(e)}"}
