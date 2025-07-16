#!/usr/bin/env python3
"""
Minimal version of Tahecho app for testing without Neo4j
"""

import os
import locale
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate

# Load environment variables
load_dotenv()

# System message
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

def setup_model():
    """Initialize the chat model"""
    try:
        model = init_chat_model("gpt-4o-mini", model_provider="openai")
        return model
    except Exception as e:
        print(f"❌ Failed to initialize model: {e}")
        return None

def create_prompt():
    """Create the prompt template"""
    return ChatPromptTemplate.from_messages([
        ("system", SYSTEM_MESSAGE),
        ("human", "{input}")
    ])

def chat_with_model(model, user_input):
    """Simple chat function"""
    try:
        prompt = create_prompt()
        chain = prompt | model
        response = chain.invoke({"input": user_input})
        return response.content
    except Exception as e:
        return f"Error: {e}"

def main():
    """Main function for minimal testing"""
    print("🚀 Tahecho Minimal Test Mode")
    print("=" * 40)
    
    # Check environment
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY not found in environment")
        print("   Please set it in your .env file")
        return
    
    # Initialize model
    print("🔧 Initializing model...")
    model = setup_model()
    if not model:
        return
    
    print("✅ Model initialized successfully!")
    print("\n💬 Chat mode (type 'quit' to exit)")
    print("-" * 40)
    
    # Simple chat loop
    while True:
        try:
            user_input = input("\nYou: ").strip()
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            
            if not user_input:
                continue
            
            print("🤖 Tahecho: ", end="", flush=True)
            response = chat_with_model(model, user_input)
            print(response)
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main() 