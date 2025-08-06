import logging
from datetime import datetime, timedelta

import pytz
from networkx import Graph

from tahecho.jira_integration.jira_client import jira_client
from tahecho.utils.graph_db import graph_db_manager

logger = logging.getLogger(__name__)


def store_changelogs(graph: Graph = None):
    """Store changelogs in the graph database if available."""
    if not graph_db_manager.is_available():
        logger.info("Graph database not available, skipping changelog storage")
        return

    graph = graph or graph_db_manager.get_graph()
    if not graph:
        logger.warning("No graph connection available for changelog storage")
        return

    important_fields = {"status", "asignee", "summary", "description"}
    events = []
    cypher_query = """
    MATCH (i:Issue)
    WHERE i.created >= datetime() - duration('P7D') OR i.updated >= datetime() - duration('P7D')
    RETURN i.key AS issue_key
    """

    issues = graph.run(cypher_query).data()
    keys = [issue["issue_key"] for issue in issues]

    for key in keys:
        issue_changelog = jira_client.get_issue_changelog(key)
        seven_days_ago = datetime.now(pytz.utc) - timedelta(days=7)
        for entry in issue_changelog.get("values", []):
            created = entry["created"]
            created_obj = datetime.strptime(created, "%Y-%m-%dT%H:%M:%S.%f%z")
            if not seven_days_ago <= created_obj <= datetime.now(pytz.utc):
                continue

            author = entry["author"]["displayName"]

            for item in entry.get("items", []):
                if item["field"] in important_fields:
                    from_string = item.get("fromString")
                    to_string = item.get("toString")
                    if from_string != to_string:
                        event = {
                            "issue_key": key,
                            "field": item["field"],
                            "from": from_string,
                            "to": to_string,
                            "author": author,
                            "timestamp": datetime.fromisoformat(created).isoformat(),
                        }
                        events.append(event)

    for event in events:
        issue_key = event["issue_key"]
        field = event["field"]
        from_val = event["from"]
        to_val = event["to"]
        author = event["author"]
        timestamp = event["timestamp"]

        query = """
        MATCH (i:Issue {key: $issue_key})
        MERGE (c:ChangeEvent {
            field: $field,
            timestamp: datetime($timestamp),
            from: $from,
            to: $to,
            author: $author
        })
        MERGE (i)-[:HAS_CHANGE]->(c)
        """

        graph.run(
            query,
            parameters={
                "issue_key": issue_key,
                "field": field,
                "from": from_val,
                "to": to_val,
                "timestamp": timestamp,
                "author": author,
            },
        )
    print("Changelogs añadidos")


def store_issues(graph: Graph = None):
    """Store issues in the graph database if available."""
    if not graph_db_manager.is_available():
        logger.info("Graph database not available, skipping issue storage")
        return

    graph = graph or graph_db_manager.get_graph()
    if not graph:
        logger.warning("No graph connection available for issue storage")
        return

    for issue in jira_client.get_all_jira_issues():
        key = issue.get("key", "")
        summary = issue.get("summary", "")
        link = issue.get("self", "")
        description = issue.get("description", "")
        created = issue.get("created", "")
        updated = issue.get("updated", "")
        issue_links = issue.get("issueLinks", "")
        cypher_query = """
        MERGE (i:Issue { key: $key })
        ON CREATE SET i.summary = $summary,
                  i.link = $link,
                  i.description = $description,
                  i.created = datetime($created),
                  i.updated = datetime($updated)
        ON MATCH SET i.summary = $summary,
                  i.link = $link,
                  i.description = $description,
                  i.created = datetime($created),
                  i.updated = datetime($updated)
        """

        graph.run(
            cypher_query,
            key=key,
            summary=summary,
            link=link,
            description=description,
            created=created,
            updated=updated,
        )

        cypher_blocks_query = """
        MERGE (a:Issue { key: $from_key })
        MERGE (b:Issue { key: $to_key })
        MERGE (a)-[:BLOCKS]->(b)
        """
        for blocker_key in issue_links.get("inwardIssue", {}).get("blocker_keys", []):
            graph.run(cypher_blocks_query, from_key=blocker_key, to_key=key)

        for blocked_key in issue_links.get("outwardIssue", {}).get("blocked_keys", []):
            graph.run(cypher_blocks_query, from_key=key, to_key=blocked_key)

    print("¡Issues insertadas/actualizadas en Neo4j!")
