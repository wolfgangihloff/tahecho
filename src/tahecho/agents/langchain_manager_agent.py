from typing import Optional

from tahecho.agents.langgraph_workflow import langgraph_workflow


class LangChainManagerAgent:
    """Manager agent using LangGraph workflow instead of SmolAgents."""

    def __init__(self):
        self.workflow = langgraph_workflow

    def run(
        self,
        user_input: str,
        reset: bool = False,
        conversation_id: Optional[str] = None,
    ) -> str:
        """
        Execute the multi-agent workflow using LangGraph.

        Args:
            user_input: The user's request
            reset: Whether to reset conversation history (not used in LangGraph)
            conversation_id: Optional conversation ID for persistence

        Returns:
            The final response from the workflow
        """
        try:
            # Execute the workflow
            result = self.workflow.execute(user_input, conversation_id)
            return result

        except Exception as e:
            return f"Manager agent execution failed: {str(e)}"


# Global instance
langchain_manager_agent = LangChainManagerAgent()
