import json
from jira_integration.jira_client import jira_client
from smolagents import Tool
from py2neo import Graph

class GetJiraIssuesTool(Tool):
    name = "get_jira_issues"
    description = "Return all the Jira issues of the site"
    inputs = {
        "query": {
            "type": "string",
            "description": "query to make the request to the neo4j database where the issues are stored"
        }
    }
    output_type = "string"
    
    def forward(self, query: str):
        uri = "bolt://localhost:7687"
        graph = Graph(uri, auth=("neo4j", "test1234"))
        
        try:
            records = graph.run(query).data()
            return json.dumps(records, indent=2)
        
        except Exception as e:
            return json.dumps({"error": str(e)})
