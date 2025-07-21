from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain.chat_models import init_chat_model
from langchain_core.messages import AIMessage
from langchain_core.tools import Tool
from langchain.agents import AgentExecutor, create_openai_tools_agent
from config import CONFIG
from agents.state import AgentState
import logging

logger = logging.getLogger(__name__)


class LangChainMCPAgent:
    """MCP Agent using LangChain for direct Jira operations."""
    
    def __init__(self):
        self.llm = init_chat_model(
            CONFIG["OPENAI_SETTINGS"]["model"], 
            model_provider="openai",
            temperature=0.1
        )
        self.system_prompt = """You are the 'mcp_agent' in a multi-agent system. Your job is to handle direct Jira operations and provide current information about issues, tasks, and project status.

You have access to Jira through MCP (Model Context Protocol) tools. You can:
- List and search for Jira issues
- Get detailed information about specific issues
- Update issue status, descriptions, and other fields
- Create new issues and subtasks
- Manage project workflows

### Your behavior:
1. Use the available MCP tools to interact with Jira directly
2. Provide clear, actionable responses based on Jira data
3. When asked about current status, fetch the latest information
4. Be helpful and efficient in managing Jira tasks
5. If you encounter errors, explain what went wrong in user-friendly terms
"""
        self.langchain_tools = self._create_mcp_tools()
        self.agent_executor = self._create_agent()
    
    def _create_mcp_tools(self):
        """Create MCP tools for Jira operations."""
        # This would be replaced with actual MCP tool creation
        # For now, we'll create a placeholder tool
        def get_jira_info(query: str) -> str:
            """Get information from Jira."""
            try:
                # This would be the actual MCP tool call
                # For now, we'll simulate an error to test error handling
                raise Exception("Failed to create generation: {\"errors\":[{\"message\":\"Invalid API key\",\"extensions\":{\"code\":\"UNEXPECTED\"}}]}")
            except Exception as e:
                logger.error(f"MCP tool execution failed: {e}")
                raise
        
        tools = [Tool(
            name="get_jira_info",
            description="Get information from Jira using MCP",
            func=get_jira_info
        )]
        return tools
    
    def _create_agent(self):
        prompt = ChatPromptTemplate.from_template(self.system_prompt + """
User request: {input}
Please use the available tools to interact with Jira and provide a helpful response.

{agent_scratchpad}
""")
        agent = create_openai_tools_agent(self.llm, self.langchain_tools, prompt)
        agent_executor = AgentExecutor(agent=agent, tools=self.langchain_tools, verbose=False)
        return agent_executor
    
    def execute(self, state: AgentState) -> AgentState:
        try:
            logger.info(f"MCP agent executing for user input: {state.user_input}")
            
            result = self.agent_executor.invoke({"input": state.user_input})
            state.agent_results["mcp_agent"] = result["output"]
            state.current_agent = "mcp_agent"
            state.messages.append(AIMessage(content=result["output"]))
            
            logger.info("MCP agent execution completed successfully")
            return state
            
        except Exception as e:
            logger.error(f"MCP agent execution failed: {e}")
            
            # Create a user-friendly error message
            error_message = self._create_user_friendly_error_message(str(e))
            
            state.agent_results["mcp_agent"] = f"Error: {str(e)}"
            state.current_agent = "mcp_agent"
            state.messages.append(AIMessage(content=error_message))
            
            return state
    
    def _create_user_friendly_error_message(self, error: str) -> str:
        """Create a user-friendly error message based on the error type."""
        error_lower = error.lower()
        
        if "invalid api key" in error_lower or "api key" in error_lower:
            return "I'm having trouble connecting to my language processing service. This might be a temporary issue. Please try again in a moment."
        elif "401" in error_lower or "unauthorized" in error_lower:
            return "I'm unable to access your Jira information right now. Please check your Jira credentials and try again."
        elif "connection" in error_lower or "timeout" in error_lower:
            return "I'm experiencing connection issues with Jira. Please try again in a moment."
        elif "not found" in error_lower or "404" in error_lower:
            return "I couldn't find the requested information in Jira. Please check the details and try again."
        else:
            return "I encountered an issue while accessing Jira. Please try again or rephrase your question."


langchain_mcp_agent = LangChainMCPAgent() 