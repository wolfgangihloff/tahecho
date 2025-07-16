from typing import Dict, List, Optional, Any
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from pydantic.v1 import BaseModel


class AgentState(BaseModel):
    """State for the multi-agent system."""
    
    # Input and conversation
    messages: List[BaseMessage] = []
    user_input: str = ""
    
    # Agent routing
    current_agent: Optional[str] = None
    agent_results: Dict[str, str] = {}
    
    # Task classification
    task_type: Optional[str] = None  # "mcp", "graph", or "general"
    
    # Final output
    final_answer: Optional[str] = None
    
    # Metadata
    conversation_id: Optional[str] = None
    timestamp: Optional[str] = None
    
    class Config:
        arbitrary_types_allowed = True
        validate_by_name = True


def create_initial_state(user_input: str, conversation_id: Optional[str] = None) -> AgentState:
    """Create initial state for a new conversation."""
    return AgentState(
        user_input=user_input,
        messages=[HumanMessage(content=user_input)],
        conversation_id=conversation_id
    ) 