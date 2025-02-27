import json
from cache import get_cached_jira_issues
from smolagents import Tool

class GetJiraIssuesTool(Tool):
    name = "get_all_jira_issues"
    description = "Return all the Jira issues of the site"
    inputs = {}
    output_type = "string"
    
    def forward(self): 
        issues = get_cached_jira_issues()
        
        if not issues or not isinstance(issues, list):
            return "No hay incidencias almacenadas."

        return json.dumps(issues, indent=2)

