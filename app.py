import json
from openai import OpenAI
from agents.manager_agent import execute_multiagent
from agents.manager_agent import manager_agent
from cache import fetch_and_cache_jira_issues, get_cached_jira_issues
from py2neo import Graph
import chainlit as cl
import locale
from config import CONFIG
from literalai import LiteralClient

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

@cl.on_chat_start
async def start():
    
    uri = "bolt://localhost:7687"
    graph = Graph(uri, auth=("neo4j", "test1234"))
    
    for issue in get_cached_jira_issues():
        key = issue.get("key", "")
        summary = issue.get("summary", "")
        link = issue.get("self", "")
        description = issue.get("description", "")
        
        cypher_query = """
        MERGE (i:Issue { key: $key })
        ON CREATE SET i.summary = $summary,
                  i.link = $link,
                  i.description = $description
        ON MATCH SET  i.summary = $summary,
                  i.link = $link,
                  i.description = $description
        """
        
        graph.run(cypher_query, 
              key=key,
              summary=summary,
              link=link,
              description=description)
    
    print("¡Issues insertadas/actualizadas en Neo4j!")
    
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
