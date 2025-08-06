from openai import OpenAI
from tahecho.agents.langchain_manager_agent import langchain_manager_agent
import chainlit as cl
import locale
import logging
from config import CONFIG
import os
from tahecho.utils.utils import store_changelogs, store_issues
from tahecho.utils.graph_db import graph_db_manager
from tahecho.utils.error_handling import setup_error_handling

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set up error handling
setup_error_handling()

# Set up LangChain tracing with LangSmith
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"

# Use environment variables directly from .env file
langchain_api_key = os.getenv("LANGCHAIN_API_KEY")
if langchain_api_key:
    os.environ["LANGCHAIN_API_KEY"] = langchain_api_key
    logger.info("LangChain API key configured from environment")
else:
    logger.info("No LangChain API key found - tracing will work without authentication")

langchain_project = os.getenv("LANGCHAIN_PROJECT", "tahecho")
os.environ["LANGCHAIN_PROJECT"] = langchain_project
logger.info(f"LangChain project set to: {langchain_project}")

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
- Create new tickets in projects
- Search for tickets using JQL queries
- Get detailed information about specific tickets

You can ask me things like:
- "What tickets are assigned to me?"
- "Please create a new ticket in project PGA with the content: Implement user authentication feature"
- "Show me all tickets in the PGA project"
- "Get details for ticket PGA-123"
"""

# Initialize OpenAI client using environment variable directly
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    logger.error("OPENAI_API_KEY not found in environment variables")
    raise ValueError("OPENAI_API_KEY environment variable is required")

client = OpenAI(api_key=openai_api_key)
logger.info("OpenAI client initialized successfully")

@cl.on_chat_start
async def start():
    # Check if graph database is enabled via environment variable
    graph_db_enabled = os.getenv("GRAPH_DB_ENABLED", "True").lower() == "true"
    
    if graph_db_enabled:
        # Attempt to connect to graph database
        graph_connected = graph_db_manager.connect()
    else:
        logger.info("Graph database disabled via environment variable")
        graph_connected = False
    
    if graph_connected:
        logger.info("Graph database connected successfully")
        # Store data in graph database
        store_issues()
        store_changelogs()
    else:
        logger.info("Graph database not available - running in limited mode")
        # Update system message to reflect limited functionality
        global SYSTEM_MESSAGE
        SYSTEM_MESSAGE += """

Note: Advanced graph-based analysis is not currently available. For complex relationship queries or historical analysis, please ensure Neo4j is running and accessible.
"""
    
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
    
    # Add information about graph database status
    if not graph_connected:
        welcome_message += "\n\nNote: Running in limited mode - advanced graph analysis features are not available."
    
    await cl.Message(welcome_message).send()

@cl.on_message
async def main(message: cl.Message):
    messages = cl.user_session.get("messages")
    
    # Add user message to history
    messages.append({"role": "user", "content": message.content})

    # Get conversation ID for persistence
    conversation_id = cl.user_session.get("conversation_id")
    if not conversation_id:
        conversation_id = f"user_{cl.user_session.get('id', 'default')}"
        cl.user_session.set("conversation_id", conversation_id)

    # Execute the LangGraph workflow
    response = langchain_manager_agent.run(message.content, conversation_id=conversation_id)
    await cl.Message(content=response).send()
    
    # Add assistant's response to history
    messages.append({"role": "assistant", "content": response})
    # Update the chat history in the session
    cl.user_session.set("messages", messages)
