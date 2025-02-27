from openai import OpenAI
from agents.jira_issues_agent import process_user_request
from cache import fetch_and_cache_jira_issues
import chainlit as cl
import locale
from config import CONFIG

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
    response = process_user_request(query)
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
    """
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        functions=functions,
        function_call="auto",
    )

    response_message = response.choices[0].message
    
    if response_message.function_call:
        function_args = json.loads(response_message.function_call.arguments)
        print(function_args)
        print(function_args["query"])
        jira_response = await call_jira_agent(function_args["query"])
        
        messages.append({"role": "assistant", "content": jira_response})
        await cl.Message(content=jira_response).send()
        return
    
    await cl.Message(content=response_message.content).send()
    # Add assistant's response to history
    messages.append({"role": "assistant", "content": response_message.content})
    """
    response = process_user_request(message.content)  
    await cl.Message(content=response).send()
    # Add assistant's response to history
    messages.append({"role": "assistant", "content": response})
    
    # Update the chat history in the session
    cl.user_session.set("messages", messages)
