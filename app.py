import os
import chainlit as cl
import locale
from openai import OpenAI
from dotenv import load_dotenv
from atlassian import Jira

# Load environment variables
load_dotenv()

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
        jql = "assignee = currentUser() ORDER BY updated DESC"
        issues = jira.jql(jql)
        
        if not issues.get('issues'):
            return "No issues found assigned to you."
            
        # Format the issues into a readable list
        formatted_issues = []
        for issue in issues['issues']:
            key = issue['key']
            summary = issue['fields']['summary']
            status = issue['fields']['status']['name']
            formatted_issues.append(f"- {key}: {summary} (Status: {status})")
            
        return "\n".join(formatted_issues)
    except Exception as e:
        return f"Error fetching Jira issues: {e}"

# Initialize OpenAI client with OpenRouter base URL and headers
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
    default_headers={
        "HTTP-Referer": "https://github.com/wolfgangIH/tahecho",
        "X-Title": "Tahecho Assistant"
    }
)

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
    
    # Check if the message is asking about Jira issues
    if any(keyword in message.content.lower() for keyword in ['jira', 'issues', 'tasks', 'assigned']):
        issues = await get_my_jira_issues()
        await cl.Message(content=issues).send()
        return
    
    # Add user message to history
    messages.append({"role": "user", "content": message.content})
    
    # Get response from OpenRouter
    response = client.chat.completions.create(
        model=os.getenv("OPENROUTER_MODEL", "anthropic/claude-3-opus-20240229"),
        messages=messages,
        stream=True,
    )
    
    # Initialize the response message
    msg = cl.Message(content="")
    
    # Stream the response
    for chunk in response:
        if chunk.choices[0].delta.content is not None:
            await msg.stream_token(chunk.choices[0].delta.content)
    
    # Send the final message
    await msg.send()
    
    # Add assistant's response to history
    messages.append({"role": "assistant", "content": msg.content})
    
    # Update the chat history in the session
    cl.user_session.set("messages", messages)
