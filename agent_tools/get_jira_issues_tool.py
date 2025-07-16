import json
from langchain_core.tools import Tool
from py2neo import Graph

def get_jira_issues(query: str) -> str:
    """Return all the Jira issues of the site"""
    uri = "bolt://neo4j:7687"
    graph = Graph(uri, auth=("neo4j", "test1234"))
    
    try:
        records = graph.run(query).data()
        cleaned = [clean_record(record) for record in records]
        return json.dumps(cleaned, indent=2)
    
    except Exception as e:
        return json.dumps({"error": str(e)})

def clean_record(record):
    cleaned = {}
    for key, value in record.items():
        if hasattr(value, 'to_native'):
            # Neo4j DateTime, convert to ISO format
            cleaned[key] = value.to_native().isoformat()
        elif isinstance(value, dict):
            cleaned[key] = clean_record(value)
        else:
            cleaned[key] = value
    return cleaned

GetJiraIssuesTool = Tool(
    name="get_jira_issues",
    description="Return all the Jira issues of the site",
    func=get_jira_issues
)
