from openai import OpenAI
from agents.langchain_manager_agent import langchain_manager_agent
import chainlit as cl
import locale
import logging
from config import CONFIG
from literalai import LiteralClient
from utils.utils import store_changelogs, store_issues
from utils.graph_db import graph_db_manager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

lai = LiteralClient(api_key="lsk_Za7jwDIUEszFc9vXyBOB99Qkz5wfRkGeRwiYcff0")
lai.instrument_openai()

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
"""

client = OpenAI(api_key=CONFIG["OPENAI_API_KEY"])

@cl.on_chat_start
async def start():
    # Attempt to connect to graph database
    graph_connected = graph_db_manager.connect()
    
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
