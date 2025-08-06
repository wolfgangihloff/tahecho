import logging
import re
from typing import Any, Dict, Optional

from langchain.chat_models import init_chat_model
from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate

from config import CONFIG
from tahecho.agents.state import AgentState

logger = logging.getLogger(__name__)


class TaskClassifier:
    """Classifies user tasks to determine which agent should handle them."""

    def __init__(self) -> None:
        openai_settings = CONFIG.get("OPENAI_SETTINGS", {})
        if not isinstance(openai_settings, dict):
            raise ValueError("OPENAI_SETTINGS must be a dictionary")
        
        model = openai_settings.get("model")
        if not isinstance(model, str):
            raise ValueError("OPENAI_SETTINGS.model must be a string")
            
        self.llm = init_chat_model(
            model, model_provider="openai", temperature=0.1
        )

        self.classification_prompt = ChatPromptTemplate.from_template(
            """
You are a task classifier for a Jira management system. Your job is to determine which specialized agent should handle the user's request.

Available agents:
1. **jira**: Handles all Jira operations using MCP (English queries)
   - "What tickets are assigned to me?"
   - "Create a new ticket in project X"
   - "Show me tickets in project Y"
   - "Get details for ticket ABC-123"
   - "Which issues are assigned to me in project PGA?"
   - JQL queries and filtering
   - Jira API operations
   - Keywords: jira, ticket, issue, assigned, project, epic, story, task, bug, sprint, backlog
   
2. **general**: General conversation or non-Jira tasks

User request: {user_input}

Analyze the request and respond with ONLY one of these exact values:
- "jira" - for all Jira operations
- "general" - for general conversation

Note: Complex relationship and dependency analysis is not currently available.

Reasoning: Provide a brief explanation of your choice.

Response format:
```json
{{
  "task_type": "jira|general",
  "reasoning": "brief explanation"
}}
```
"""
        )

    def classify_task(self, state: AgentState) -> AgentState:
        """Classify the task and update the state."""
        try:
            # Check for conversation context first
            context_classification = self._check_conversation_context(state)
            if context_classification:
                state.task_type = context_classification
                state.messages.append(
                    AIMessage(
                        content=f"Task classified as: {context_classification}. Reasoning: Continuing previous Jira conversation"
                    )
                )
                return state

            # Create the classification chain
            chain = self.classification_prompt | self.llm

            # Get classification
            result = chain.invoke({"user_input": state.user_input})

            # First, try keyword-based classification as fallback for reliability
            user_input_lower = state.user_input.lower()
            jira_keywords = ["jira", "ticket", "issue", "assigned", "project", 
                           "epic", "story", "task", "bug", "sprint", "backlog"]
            
            if any(keyword in user_input_lower for keyword in jira_keywords):
                task_type = "jira"
                reasoning = f"Detected Jira-related keywords"
                
                # Update state
                state.task_type = task_type
                state.messages.append(
                    AIMessage(
                        content=f"Task classified as: {task_type}. Reasoning: {reasoning}"
                    )
                )
                return state

            # Parse the response (assuming it's in JSON format)
            import json

            # Extract JSON from the response
            json_match = re.search(r"\{.*\}", result.content.strip(), re.DOTALL)

            if json_match:
                try:
                    classification = json.loads(json_match.group())
                    task_type = classification.get("task_type", "general")
                    reasoning = classification.get("reasoning", "")
                except Exception:
                    # If JSON parsing fails, fallback to keyword search
                    content = json_match.group()
                    if "jira" in content.lower():
                        task_type = "jira"
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
                    # Fallback: try to extract task type from response and check for German/English keywords
                    content = result.content.lower()
                    user_input_lower = state.user_input.lower()
                    
                    # Check for Jira-related keywords in English
                    jira_keywords = ["jira", "ticket", "issue", "assigned", "project", 
                                   "epic", "story", "task", "bug", "sprint", "backlog"]
                    
                    if any(keyword in user_input_lower for keyword in jira_keywords) or "jira" in content:
                        task_type = "jira"
                    else:
                        task_type = "general"
                    reasoning = result.content

            # Update state
            state.task_type = task_type
            state.messages.append(
                AIMessage(
                    content=f"Task classified as: {task_type}. Reasoning: {reasoning}"
                )
            )

            return state

        except Exception as e:
            logger.error(f"Task classification failed: {e}")
            
            # Fallback to general if classification fails
            state.task_type = "general"
            state.messages.append(
                AIMessage(
                    content=f"Task classification failed, defaulting to general: {str(e)}"
                )
            )
            return state

    def _check_conversation_context(self, state: AgentState) -> Optional[str]:
        """Check if this is a follow-up to a previous Jira conversation."""
        if not state.messages or len(state.messages) < 2:
            return None
            
        # Look at recent messages for Jira context
        recent_messages = state.messages[-5:]  # Check last 5 messages
        
        for message in recent_messages:
            if hasattr(message, 'content') and message.content:
                content_lower = message.content.lower()
                
                # Check for Jira-related context indicators
                jira_context_indicators = [
                    "jira", "ticket", "assigned", "username", "email address",
                    "project key", "search for tickets", "mcp integration",
                    "clarification needed", "could you please tell me"
                ]
                
                if any(indicator in content_lower for indicator in jira_context_indicators):
                    # Check if current input looks like a follow-up response
                    user_input_lower = state.user_input.lower()
                    
                    # Common follow-up patterns
                    follow_up_patterns = [
                        # Username/email patterns
                        r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$',  # email
                        r'^[a-zA-Z][a-zA-Z0-9._-]{2,20}$',  # username-like (includes wolfgang.ihloff)
                        r'^[a-zA-Z][a-zA-Z0-9._-]*\.[a-zA-Z][a-zA-Z0-9._-]*$',  # dotted usernames like wolfgang.ihloff
                        # Project key patterns
                        r'^[A-Z]{2,10}$',  # project key like PGA, PROJ
                        # Simple confirmations
                        r'^(yes|y|no|n|ok|okay|sure)$'
                    ]
                    
                    if (any(re.match(pattern, state.user_input.strip(), re.IGNORECASE) for pattern in follow_up_patterns) or
                        len(state.user_input.strip().split()) <= 3):  # Short responses likely follow-ups
                        return "jira"
                        
        return None


# Global instance - lazy initialization
_task_classifier_instance = None


def get_task_classifier() -> TaskClassifier:
    """Get the global task classifier instance, creating it if needed."""
    global _task_classifier_instance
    if _task_classifier_instance is None:
        _task_classifier_instance = TaskClassifier()
    return _task_classifier_instance


# For backward compatibility - this will be set when first accessed
task_classifier = None


def __getattr__(name: str) -> TaskClassifier:
    """Lazy load the task_classifier when first accessed."""
    if name == "task_classifier":
        return get_task_classifier()
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
