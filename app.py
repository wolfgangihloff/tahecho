from openai import OpenAI
from agents.langchain_manager_agent import langchain_manager_agent
from py2neo import Graph
import chainlit as cl
import locale
from config import CONFIG
from literalai import LiteralClient
from utils.utils import store_changelogs, store_issues

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
    
    uri = "bolt://neo4j:7687"
    graph = Graph(uri, auth=("neo4j", "test1234"))
    """
    driver = GraphDatabase.driver(uri, auth=("neo4j", "test1234"))
    INDEX_NAME = "index-name"
    embedder = OpenAIEmbeddings(model="text-embedding-3-large")
    retriever = VectorRetriever(driver, INDEX_NAME, embedder)
    llm = OpenAILLM(model_name="gpt-4o", model_params={"temperature": 0})
    rag = GraphRAG(retriever=retriever, llm=llm)
    """
    
    store_issues(graph)
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
