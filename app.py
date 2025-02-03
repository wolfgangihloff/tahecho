import os
import chainlit as cl
import locale
from openai import OpenAI
from dotenv import load_dotenv
from atlassian import Jira
import requests
from requests.auth import HTTPBasicAuth


# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

cl.instrument_openai()

settings = {
    "model": "gpt-4o",
    "temperature": 0.7,
    "max_tokens": 1000,
    "top_p": 1,
    "frequency_penalty": 0,
    "presence_penalty": 0,
    "stream": False,
}

# Initialize Jira client
jira = None
try:
    jira = Jira(
        url=os.getenv('JIRA_INSTANCE_URL'),
        username=os.getenv('JIRA_USERNAME'),
        password=os.getenv('JIRA_API_TOKEN'),
        cloud=os.getenv('JIRA_CLOUD', 'True').lower() == 'true'
    )
except Exception as e:
    print(f"Failed to initialize Jira client: {e}")

async def get_my_jira_issues():
    """Get issues assigned to the current user"""
    if not jira:
        return "Jira client is not initialized. Please check your environment variables."
    try:
        # JQL query to find issues assigned to the current user
        
        jql = "assignee = currentUser() ORDER BY created DESC"
        issues = jira.jql(jql)
        
        if not issues.get('issues'):
            return "No issues found assigned to you."
            
        # Format the issues into a readable list
        formatted_issues = []
        for issue in issues['issues']:
            print(f"Tarea: {issue['fields']['summary']}\n")
            print(f"Description: {issue['fields']['description']}\n")
            key = issue['key']
            summary = issue['fields']['summary']
            status = issue['fields']['status']['name']
            formatted_issues.append(f"- {key}: {summary} (Status: {status})")
            
        return "\n".join(formatted_issues)
    except Exception as e:
        return f"Error fetching Jira issues: {e}"
    

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

    response = client.chat.completions.create(
        messages = messages,
        functions=functions,
        function_call="auto",
        **settings
    )

    if response.choices[0].message.function_call:
        function_name = response.choices[0].message.function_call.name
        if function_name == "get_my_jira_issues":
            # Call the function to get Jira issues
            issues = await get_my_jira_issues()
            await cl.Message(content=f"Here are your Jira issues:\n{issues}").send()
            return

    # If no function call, send the assistant's response
    assistant_response = response.choices[0].message.content
    await cl.Message(content=assistant_response).send()    
    # Add assistant's response to history
    messages.append({"role": "assistant", "content": assistant_response})
    
    # Update the chat history in the session
    cl.user_session.set("messages", messages)
