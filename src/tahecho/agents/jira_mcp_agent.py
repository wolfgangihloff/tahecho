import asyncio
import json
import logging
import os
import subprocess
import tempfile
from typing import Any, Dict, List, Optional

from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.chat_models import init_chat_model
from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import Tool

from config import CONFIG
from tahecho.agents.state import AgentState

logger = logging.getLogger(__name__)


class JiraMCPAgent:
    """Jira Agent using MCP Atlassian server for Jira operations."""

    def __init__(self):
        self.llm = init_chat_model(
            CONFIG["OPENAI_SETTINGS"]["model"], model_provider="openai", temperature=0.1
        )
        self.system_prompt = """You are a Jira assistant that helps users manage their Jira tickets and projects. You have access to Jira through MCP (Model Context Protocol) tools.

You can:
- Search for tickets assigned to users using jira_search
- Get detailed information about specific issues using jira_get_issue
- Create new tickets in projects using jira_create_issue
- Update existing tickets using jira_update_issue
- Add comments to tickets using jira_add_comment
- Transition tickets between statuses using jira_transition_issue

### Your behavior:
1. Use the available MCP tools to interact with Jira directly
2. When asked about tickets assigned to a user, use jira_search with JQL "assignee = currentUser()"
3. When creating tickets, use jira_create_issue with proper project key and issue type
4. Provide clear, actionable responses based on Jira data
5. If you encounter errors, explain what went wrong in user-friendly terms
6. Always confirm actions before executing them

### Common JQL queries:
- Tickets assigned to current user: "assignee = currentUser()"
- Tickets in specific project: "project = 'PGA'"
- Open tickets: "status != 'Done' AND status != 'Closed'"
- My open tickets: "assignee = currentUser() AND status != 'Done' AND status != 'Closed'"
"""
        self.mcp_tools = self._create_mcp_tools()
        self.agent_executor = self._create_agent()
        self.mcp_process = None

    def _start_mcp_server(self):
        """Start the MCP Atlassian server process."""
        if self.mcp_process and self.mcp_process.poll() is None:
            return True  # Server already running
        
        try:
            cmd = [
                "uvx", "mcp-atlassian",
                "--jira-url", CONFIG["JIRA_INSTANCE_URL"],
                "--jira-username", CONFIG["JIRA_USERNAME"],
                "--jira-token", CONFIG["JIRA_API_TOKEN"],
                "--enabled-tools", "jira_search,jira_get_issue,jira_create_issue,jira_get_all_projects,jira_add_comment,jira_transition_issue"
            ]
            
            # For Jira Cloud, no additional flag is needed
            # The --jira-token and --jira-username flags indicate Cloud authentication
            
            logger.info("Starting MCP Atlassian server...")
            self.mcp_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Give it a moment to start
            import time
            time.sleep(3)
            
            if self.mcp_process.poll() is None:
                logger.info("✅ MCP Atlassian server started successfully")
                return True
            else:
                stdout, stderr = self.mcp_process.communicate()
                logger.error(f"❌ MCP server failed to start")
                logger.error(f"STDOUT: {stdout}")
                logger.error(f"STDERR: {stderr}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error starting MCP server: {e}")
            return False

    def _stop_mcp_server(self):
        """Stop the MCP Atlassian server process."""
        if self.mcp_process and self.mcp_process.poll() is None:
            logger.info("Stopping MCP Atlassian server...")
            self.mcp_process.terminate()
            try:
                self.mcp_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.mcp_process.kill()
            logger.info("✅ MCP Atlassian server stopped")

    def _create_mcp_tools(self) -> List[Tool]:
        """Create MCP tools for Jira operations."""
        
        def search_my_tickets(query: str = "") -> str:
            """Search for tickets assigned to the current user."""
            try:
                if not self._start_mcp_server():
                    return "Error: Unable to start MCP server"
                
                # For now, we'll simulate the MCP tool call
                # In a real implementation, this would communicate with the MCP server
                return "Found 3 tickets assigned to you:\n1. PGA-123: Implement new feature (In Progress)\n2. PGA-456: Fix bug in login (To Do)\n3. PGA-789: Review documentation (Done)"
            except Exception as e:
                logger.error(f"Failed to search tickets: {e}")
                return f"Error searching tickets: {str(e)}"

        def create_ticket(project_key: str, summary: str, description: str = "", issue_type: str = "Task") -> str:
            """Create a new ticket in the specified project."""
            try:
                if not self._start_mcp_server():
                    return "Error: Unable to start MCP server"
                
                # For now, we'll simulate the MCP tool call
                # In a real implementation, this would communicate with the MCP server
                ticket_id = f"{project_key}-{hash(summary) % 1000}"
                return f"Successfully created ticket {ticket_id}: {summary}"
            except Exception as e:
                logger.error(f"Failed to create ticket: {e}")
                return f"Error creating ticket: {str(e)}"

        def get_ticket_details(ticket_key: str) -> str:
            """Get detailed information about a specific ticket."""
            try:
                if not self._start_mcp_server():
                    return "Error: Unable to start MCP server"
                
                # For now, we'll simulate the MCP tool call
                return f"Ticket {ticket_key} details:\n- Status: In Progress\n- Assignee: Current User\n- Priority: Medium\n- Description: {ticket_key} details"
            except Exception as e:
                logger.error(f"Failed to get ticket details: {e}")
                return f"Error getting ticket details: {str(e)}"

        def search_tickets(jql_query: str) -> str:
            """Search for tickets using JQL query."""
            try:
                if not self._start_mcp_server():
                    return "Error: Unable to start MCP server"
                
                # For now, we'll simulate the MCP tool call
                if "currentUser" in jql_query:
                    return "Found 3 tickets assigned to you:\n1. PGA-123: Implement new feature (In Progress)\n2. PGA-456: Fix bug in login (To Do)\n3. PGA-789: Review documentation (Done)"
                elif "PGA" in jql_query:
                    return "Found 5 tickets in PGA project:\n1. PGA-123: Implement new feature (In Progress)\n2. PGA-456: Fix bug in login (To Do)\n3. PGA-789: Review documentation (Done)\n4. PGA-101: Update documentation (To Do)\n5. PGA-202: Test new feature (In Progress)"
                else:
                    return f"Search results for '{jql_query}': No tickets found matching the criteria."
            except Exception as e:
                logger.error(f"Failed to search tickets: {e}")
                return f"Error searching tickets: {str(e)}"

        tools = [
            Tool(
                name="search_my_tickets",
                description="Search for tickets assigned to the current user",
                func=search_my_tickets,
            ),
            Tool(
                name="search_tickets",
                description="Search for tickets using JQL query. Args: jql_query (str)",
                func=search_tickets,
            ),
            Tool(
                name="create_ticket",
                description="Create a new ticket in a project. Args: project_key (str), summary (str), description (str, optional), issue_type (str, optional, default='Task')",
                func=create_ticket,
            ),
            Tool(
                name="get_ticket_details",
                description="Get detailed information about a specific ticket. Args: ticket_key (str)",
                func=get_ticket_details,
            ),
        ]
        return tools

    def _create_agent(self):
        prompt = ChatPromptTemplate.from_template(
            self.system_prompt
            + """
User request: {input}
Please use the available tools to interact with Jira and provide a helpful response.

{agent_scratchpad}
"""
        )
        agent = create_openai_tools_agent(self.llm, self.mcp_tools, prompt)
        agent_executor = AgentExecutor(
            agent=agent, tools=self.mcp_tools, verbose=False
        )
        return agent_executor

    def execute(self, state: AgentState) -> AgentState:
        try:
            logger.info(f"Jira MCP agent executing for user input: {state.user_input}")

            result = self.agent_executor.invoke({"input": state.user_input})
            state.agent_results["jira_mcp_agent"] = result["output"]
            state.current_agent = "jira_mcp_agent"
            state.messages.append(AIMessage(content=result["output"]))

            logger.info("Jira MCP agent execution completed successfully")
            return state

        except Exception as e:
            logger.error(f"Jira MCP agent execution failed: {e}")

            # Create a user-friendly error message
            error_message = self._create_user_friendly_error_message(str(e))

            state.agent_results["jira_mcp_agent"] = f"Error: {str(e)}"
            state.current_agent = "jira_mcp_agent"
            state.messages.append(AIMessage(content=error_message))

            return state

    def _create_user_friendly_error_message(self, error: str) -> str:
        """Create a user-friendly error message based on the error type."""
        error_lower = error.lower()

        if "invalid api key" in error_lower or "api key" in error_lower:
            return "I'm having trouble connecting to Jira. Please check your Jira credentials in the configuration."
        elif "401" in error_lower or "unauthorized" in error_lower:
            return "I'm unable to access your Jira information. Please check your Jira credentials and try again."
        elif "connection" in error_lower or "timeout" in error_lower:
            return "I'm experiencing connection issues with Jira. Please try again in a moment."
        elif "not found" in error_lower or "404" in error_lower:
            return "I couldn't find the requested information in Jira. Please check the details and try again."
        elif "project" in error_lower and "not found" in error_lower:
            return "The specified project was not found. Please check the project key and try again."
        else:
            return "I encountered an issue while accessing Jira. Please try again or rephrase your question."

    def __del__(self):
        """Cleanup when the agent is destroyed."""
        self._stop_mcp_server()


jira_mcp_agent = JiraMCPAgent()
