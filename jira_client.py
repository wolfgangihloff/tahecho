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

    async def get_my_jira_issues(self):
        """Get Jira issues assigned to the current user"""
        if not self.jira:
            return "Jira client is not initialized. Check environment variables."

        try:
            jql = "assignee = currentUser() ORDER BY created DESC"
            issues = self.jira.jql(jql)

            if not issues.get('issues'):
                return "No issues found assigned to you."

            # Format response
            formatted_issues = []
            for issue in issues["issues"]:
                key = issue["key"]
                summary = issue["fields"]["summary"]
                status = issue["fields"]["status"]["name"]
                formatted_issues.append(f"- {key}: {summary} (Status: {status})")

            return "\n".join(formatted_issues)
        except Exception as e:
            return f"Error fetching Jira issues: {e}"

# Instantiate the client
jira_client = JiraClient()
