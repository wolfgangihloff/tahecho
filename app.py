from agent import process_user_request
import chainlit as cl
import locale
from intent_handler import handle_function_call
from config import CONFIG
from jira_client import JiraClient
from openai_client import get_openai_response



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

@cl.on_chat_start
async def start():
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
    # Get the chat history
    messages = cl.user_session.get("messages")
    
    # Add user message to history
    messages.append({"role": "user", "content": message.content})

    functions = [
        {
            "name": "get_my_jira_issues",
            "description": "Retrieve a list of Jira issues assigned to the current user.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    ]

    response = process_user_request(message.content)  
    await cl.Message(content=response).send()
    # Add assistant's response to history
    messages.append({"role": "assistant", "content": response})
    
    # Update the chat history in the session
    cl.user_session.set("messages", messages)
