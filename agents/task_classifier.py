from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain.chat_models import init_chat_model
from config import CONFIG
from agents.state import AgentState
from langchain_core.messages import AIMessage


class TaskClassifier:
    """Classifies user tasks to determine which agent should handle them."""
    
    def __init__(self):
        self.llm = init_chat_model(
            CONFIG["OPENAI_SETTINGS"]["model"], 
            model_provider="openai",
            temperature=0.1
        )
        
        self.classification_prompt = ChatPromptTemplate.from_template("""
You are a task classifier for a Jira management system. Your job is to determine which specialized agent should handle the user's request.

Available agents:
1. **mcp_agent**: Handles direct Jira operations
   - Creating, updating, or retrieving Jira issues
   - JQL queries and filtering
   - Status changes and field updates
   - Direct Jira API operations
   
2. **graph_agent**: Handles complex reasoning and relationships
   - Dependency analysis ("Why is this blocked?")
   - Historical analysis ("What changed this week?")
   - Relationship queries ("What depends on X?")
   - Project summaries and overviews
   - Semantic search and pattern recognition

3. **general**: General conversation or non-Jira tasks

User request: {user_input}

Analyze the request and respond with ONLY one of these exact values:
- "mcp" - for direct Jira operations
- "graph" - for complex reasoning and relationships  
- "general" - for general conversation

Reasoning: Provide a brief explanation of your choice.

Response format:
```json
{
  "task_type": "mcp|graph|general",
  "reasoning": "brief explanation"
}
```
""")
    
    def classify_task(self, state: AgentState) -> AgentState:
        """Classify the task and update the state."""
        try:
            # Create the classification chain
            chain = self.classification_prompt | self.llm
            
            # Get classification
            result = chain.invoke({"user_input": state.user_input})
            
            # Parse the response (assuming it's in JSON format)
            import json
            import re
            
            # Extract JSON from the response
            json_match = re.search(r'\{.*\}', result.content.strip(), re.DOTALL)
            
            if json_match:
                try:
                    classification = json.loads(json_match.group())
                    task_type = classification.get("task_type", "general")
                    reasoning = classification.get("reasoning", "")
                except Exception:
                    # If JSON parsing fails, fallback to keyword search
                    content = json_match.group()
                    if "mcp" in content.lower():
                        task_type = "mcp"
                    elif "graph" in content.lower():
                        task_type = "graph"
                    else:
                        task_type = "general"
                    reasoning = content
            else:
                # Try to parse the entire string as JSON
                try:
                    classification = json.loads(result.content.strip())
                    task_type = classification.get("task_type", "general")
                    reasoning = classification.get("reasoning", "")
                except Exception:
                    # Fallback: try to extract task type from response
                    content = result.content
                    if "mcp" in content.lower():
                        task_type = "mcp"
                    elif "graph" in content.lower():
                        task_type = "graph"
                    else:
                        task_type = "general"
                    reasoning = content
            
            # Update state
            state.task_type = task_type
            state.messages.append(AIMessage(content=f"Task classified as: {task_type}. Reasoning: {reasoning}"))
            
            return state
            
        except Exception as e:
            # Fallback to general if classification fails
            state.task_type = "general"
            state.messages.append(AIMessage(content=f"Task classification failed, defaulting to general: {str(e)}"))
            return state


# Global instance - will be created when needed
task_classifier = None 