import json
from jira_integration.jira_client import jira_client
from smolagents import Tool

class GetIssuesByJQLTool(Tool):
    name = "get_issues_with_jql_request"
    description = "Return Jira issues from a jql request to Jira API."
    inputs = {
        "jql": {
            "type": "string",
            "description": "JQL query to filter issues"
        },
        "maxResults": {
            "type": "integer",
            "description": "Number of results returned by the API, if not specified by default should be 50"
        }
    }
    output_type = "string"
    
    def forward(self, jql, maxResults): 
        """
        Get Jira issues using a JQL query.
        
        Args:
            jql (str): JQL query to filter issues
            maxResults (int): Number of results returned by the API, if not specified by default should be 50
            
        Returns:
            str: JSON string containing the filtered issues
        """
        try:
            # Get the Jira instance
            jira_instance = jira_client.get_instance()
            
            if not jira_instance:
                return "Error: Jira client not initialized."
            
            # Make the JQL query
            issues = jira_instance.jql(jql, limit=maxResults)
            
            if not issues.get('issues'):
                return "No issues found matching the query."
            
            # Filter and format the issues
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
            
            return json.dumps(filtered_issues, indent=2)
        except Exception as e:
            return f"Error getting issues by JQL: {str(e)}"
