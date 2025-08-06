import json
import logging

from langchain_core.tools import Tool

from tahecho.utils.graph_db import graph_db_manager

logger = logging.getLogger(__name__)


def get_jira_issues(query: str) -> str:
    """Return all the Jira issues of the site"""
    if not graph_db_manager.is_available():
        return json.dumps(
            {
                "error": "Graph database not available",
                "message": "Neo4j is not connected. Please ensure the graph database is running and accessible.",
            }
        )

    try:
        records = graph_db_manager.run_query(query)
        if records is None:
            return json.dumps({"error": "Failed to execute query"})

        cleaned = [clean_record(record) for record in records]
        return json.dumps(cleaned, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e)})


def clean_record(record):
    cleaned = {}
    for key, value in record.items():
        if hasattr(value, "to_native"):
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
    func=get_jira_issues,
)
