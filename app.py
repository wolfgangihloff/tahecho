from datetime import datetime, timedelta
import json
import os
from neo4j import GraphDatabase
from neo4j_graphrag.embeddings import OpenAIEmbeddings
from neo4j_graphrag.retrievers import VectorRetriever
from neo4j_graphrag.llm import OpenAILLM
from neo4j_graphrag.generation import GraphRAG
from openai import OpenAI
import pytz
from agents.manager_agent import execute_multiagent
from agents.manager_agent import manager_agent
from cache import fetch_and_cache_jira_issues, get_cached_jira_issues
from py2neo import Graph
import chainlit as cl
import locale
from config import CONFIG
from literalai import LiteralClient
from jira_integration.jira_client import jira_client

lai = LiteralClient(api_key="lsk_Za7jwDIUEszFc9vXyBOB99Qkz5wfRkGeRwiYcff0")
lai.instrument_openai()

fetch_and_cache_jira_issues()

# System message to set the context
SYSTEM_MESSAGE = """You are Tahecho, a personal assistant focused on helping users with:
1. Jira task management and updates
2. Personal todo list organization
3. Calendar management
4. Email assistance

You aim to be efficient and practical, staying out of the user interface when possible. 
You provide clear, actionable responses and can help with both specific tasks and general productivity questions.

For Jira functionality, you can:
- List all issues assigned to the current user
- Show issue details and status updates
- Help manage and track Jira tasks efficiently

When users ask about their Jira issues or tasks, you can use the get_my_jira_issues() function to retrieve and display their assigned issues."""

client = OpenAI(api_key=CONFIG["OPENAI_API_KEY"])

async def call_jira_agent(query: any):
    #response = process_user_request(query)
    response = execute_multiagent(query)
    return response

functions = [
        {
            "name": "call_jira_agent",
            "description": "Executes the agent that returns information about the Jira issues and can create new Jira issues.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                    "description": "The user message that describes the Jira information requested or the details for the creation of an issue.",    
                    },
                },
                "required": ["query"]
            }
        }
    ]

def store_changelogs(graph: Graph):
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
                            "timestamp": datetime.fromisoformat(created).isoformat()
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

        graph.run(query, parameters={
            "issue_key": issue_key,
            "field": field,
            "from": from_val,
            "to": to_val,
            "timestamp": timestamp,
            "author": author
    })
    print("Changelogs añadidos")
        


@cl.on_chat_start
async def start():
    
    uri = "bolt://localhost:7687"
    graph = Graph(uri, auth=("neo4j", "test1234"))
    """
    driver = GraphDatabase.driver(uri, auth=("neo4j", "test1234"))
    INDEX_NAME = "index-name"
    embedder = OpenAIEmbeddings(model="text-embedding-3-large")
    retriever = VectorRetriever(driver, INDEX_NAME, embedder)
    llm = OpenAILLM(model_name="gpt-4o", model_params={"temperature": 0})
    rag = GraphRAG(retriever=retriever, llm=llm)
    """
    
    for issue in get_cached_jira_issues():
        key = issue.get("key", "")
        summary = issue.get("summary", "")
        link = issue.get("self", "")
        description = issue.get("description", "")
        created = issue.get("created", "")
        updated = issue.get("updated", "")
        
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
        
        graph.run(cypher_query,
              key=key,
              summary=summary,
              link=link,
              description=description,
              created = created,
              updated = updated
              )
    
    print("¡Issues insertadas/actualizadas en Neo4j!")
    store_changelogs(graph)
    
    # Initialize chat with system message
    cl.user_session.set("messages", [
        {"role": "system", "content": SYSTEM_MESSAGE}
    ])
    
    system_locale = locale.getdefaultlocale()[0]
    welcome_message = (
        "Willkommen bei Tahecho! Wie kann ich Ihnen heute helfen?"
        if system_locale.startswith('de')
        else "Welcome to Tahecho! How can I assist you today?"
    )
    await cl.Message(welcome_message).send()

@cl.on_message
async def main(message: cl.Message):
    messages = cl.user_session.get("messages")
    
    # Add user message to history
    messages.append({"role": "user", "content": message.content})

    response = await execute_multiagent(message.content)
    await cl.Message(content=response).send()
    # Add assistant's response to history
    messages.append({"role": "assistant", "content": response})
    # Update the chat history in the session
    cl.user_session.set("messages", messages)
