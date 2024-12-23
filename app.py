import os
import chainlit as cl
import locale
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize OpenAI client with OpenRouter base URL and headers
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
    default_headers={
        "HTTP-Referer": "https://github.com/wolfgangIH/tohecho",
        "X-Title": "Tohecho Assistant"
    }
)

# System message to set the context
SYSTEM_MESSAGE = """You are Tohecho, a personal assistant focused on helping users with:
1. Jira task management and updates
2. Personal todo list organization
3. Calendar management
4. Email assistance

You aim to be efficient and practical, staying out of the user interface when possible. 
You provide clear, actionable responses and can help with both specific tasks and general productivity questions."""

@cl.on_chat_start
async def start():
    # Initialize chat with system message
    cl.user_session.set("messages", [
        {"role": "system", "content": SYSTEM_MESSAGE}
    ])
    
    system_locale = locale.getdefaultlocale()[0]
    welcome_message = (
        "Willkommen bei Tohecho! Wie kann ich Ihnen heute helfen?"
        if system_locale.startswith('de')
        else "Welcome to tohecho! How can I assist you today?"
    )
    await cl.Message(welcome_message).send()

@cl.on_message
async def main(message: str):
    # Get the chat history
    messages = cl.user_session.get("messages")
    
    # Add user message to history
    messages.append({"role": "user", "content": message})
    
    # Get response from OpenRouter
    response = client.chat.completions.create(
        model=os.getenv("OPENROUTER_MODEL", "anthropic/claude-3-opus-20240229"),
        messages=messages,
        stream=True,
    )
    
    # Initialize the response message
    msg = cl.Message(content="")
    
    # Stream the response
    async for chunk in response:
        if chunk.choices[0].delta.content:
            await msg.stream_token(chunk.choices[0].delta.content)
    
    # Send the final message
    await msg.send()
    
    # Add assistant's response to history
    messages.append({"role": "assistant", "content": msg.content})
    
    # Update the chat history in the session
    cl.user_session.set("messages", messages)
