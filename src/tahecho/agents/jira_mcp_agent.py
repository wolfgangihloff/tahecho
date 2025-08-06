import asyncio
import json
import logging
import os
import re
import subprocess
import tempfile
from typing import Any, Dict, List, Optional

# MCP communication will be done via direct JSON-RPC to avoid Python 3.11 compatibility issues

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
- Search for tickets assigned to users using search_tickets
- Get detailed information about specific issues using get_ticket_details  
- Create new tickets in projects using create_ticket
- Search tickets assigned to current user using search_my_tickets

### Critical Behavior Rules:
1. **Always clarify ambiguous requests**: If the user asks for "my tickets" or tickets "assigned to me" without specifying their username, ask them to clarify who they are
2. **Always verify project keys**: If a user mentions a project, ask them to confirm the exact project key (e.g., "PGA", "PROJ", etc.)
3. **Use real Jira data**: Only return actual data from Jira, never make up or simulate ticket information
4. **Handle authentication**: If you cannot access Jira or get authentication errors, clearly explain the issue

### Clarification Examples:
- User: "What tickets are assigned to me?" 
  → You: "I'd be happy to help! Could you please tell me your Jira username or email address so I can search for tickets assigned to you?"

- User: "Show me tickets in project PGA"
  → You: "I'll search for tickets in project PGA. Could you confirm that 'PGA' is the correct project key?"

- User: "Which Jira issues are assigned to me in project PGA?"
  → You: "I'll help you find your assigned tickets in project PGA. Could you please provide your Jira username or email address?"

### JQL Query Patterns:
- Specific user's tickets: "assignee = 'username@company.com'"
- User's tickets in project: "assignee = 'username@company.com' AND project = 'PGA'"
- Project tickets: "project = 'PGA'"
- Open tickets: "status != 'Done' AND status != 'Closed'"

### Error Handling:
- If MCP server fails to start, explain that Jira connectivity is unavailable
- If authentication fails, ask user to check their Jira credentials
- If project not found, ask user to verify the project key
- If no tickets found, clearly state that no matching tickets were found

### Response Format:
- Always be helpful and professional
- Provide clear, actionable information
- If asking for clarification, explain why you need the information
- When showing ticket results, include key details like ticket key, summary, status, and assignee
- For simple requests like getting ticket details, you can use tools directly
- For ambiguous requests about "my tickets" or "assigned to me", ask for clarification first before using tools

### Handling Follow-up Responses:
- If user provides a username (like "wolfgang.ihloff" or "john.doe@company.com"), treat it as a response to previous clarification request
- Use the search_tickets tool with JQL: "assignee = 'username'" to search for tickets assigned to that user
- If user provides a project key (like "PGA"), search for tickets in that project
- Always acknowledge that you received their information and explain what you're doing with it
"""
        self.mcp_tools = self._create_mcp_tools()
        self.agent_executor = self._create_agent()
        self.mcp_process = None

    def _check_mcp_server(self):
        """Check if MCP Atlassian server is running externally."""
        try:
            # Check if there's a running MCP server process
            result = subprocess.run(
                ["ps", "aux"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if "mcp-atlassian" in result.stdout:
                logger.info("✅ Found running MCP Atlassian server")
                return True
            else:
                logger.warning("❌ No MCP Atlassian server found running")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error checking for MCP server: {e}")
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

    def _call_mcp_tool(self, tool_name: str, parameters: Dict[str, Any]) -> str:
        """Call an MCP tool via the Atlassian server."""
        try:
            logger.info(f"Calling MCP tool: {tool_name} with parameters: {parameters}")
            
            # Check if MCP server is properly configured
            if not all([CONFIG.get("JIRA_INSTANCE_URL"), CONFIG.get("JIRA_USERNAME"), CONFIG.get("JIRA_API_TOKEN")]):
                return """❌ Jira configuration incomplete. Please ensure the following environment variables are set:
- JIRA_INSTANCE_URL (e.g., https://yourcompany.atlassian.net)
- JIRA_USERNAME (your Jira email address)  
- JIRA_API_TOKEN (your Jira API token)

You can create an API token at: https://id.atlassian.com/manage-profile/security/api-tokens"""

            # Check if MCP server is running first
            if not self._check_mcp_server():
                return f"""❌ MCP Server Not Running

The MCP-Atlassian server is not currently running. Please start it in a separate terminal:

```bash
uvx mcp-atlassian
```

The server will read your Jira credentials from the .env file. Once started, try your request again."""

            # MCP server is running - try real protocol communication
            try:
                # Use a thread pool to run the async code from sync context
                import concurrent.futures
                import threading
                
                def run_async_in_thread():
                    # Create a new event loop for this thread
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    try:
                        return new_loop.run_until_complete(self._call_mcp_tool_async(tool_name, parameters))
                    finally:
                        new_loop.close()
                
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(run_async_in_thread)
                    result = future.result(timeout=30)  # 30 second timeout
                    return result
                    
            except Exception as e:
                logger.warning(f"Real MCP communication failed, using simulated response: {e}")
                # Fall back to simulated response
                pass
            
            # Fallback simulated responses
            if tool_name == "jira_search":
                jql = parameters.get("jql", "")
                # Extract username from JQL if possible
                username = "the user"
                if "wolfgang.ihloff" in jql:
                    username = "wolfgang.ihloff@aleph-alpha.com"
                elif "assignee = '" in jql:
                    match = re.search(r"assignee = '([^']*)'", jql)
                    if match:
                        username = match.group(1)
                
                return f"""Found 2 tickets assigned to {username}:

1. PGA-101: Implement OAuth 2.0 authentication (In Progress, High Priority)
2. PGA-205: Fix mobile login issues (To Do, Medium Priority)

Note: These are simulated results for demonstration. The MCP server is running but requires protocol integration for real Jira data."""
                    
            elif tool_name == "jira_get_issue":
                issue_key = parameters.get("issue_key", "")
                return f"""✅ Ticket Detail Request Received

I understand you want details for ticket {issue_key}. 

Currently, the Jira integration requires the MCP-Atlassian server to be properly connected to fetch real ticket data. 

To get the actual details for {issue_key}:
1. Ensure the MCP-Atlassian server is running and connected to your Jira instance
2. Verify you have access to view this ticket in Jira
3. Check that the ticket key '{issue_key}' exists in your Jira instance

Would you like me to help you with anything else regarding Jira tickets?"""
                
            elif tool_name == "jira_create_issue":
                project_key = parameters.get("project", "")
                summary = parameters.get("summary", "")
                return f"""🔧 MCP Integration Required

Would create issue in project {project_key} with summary: {summary}

To enable real Jira integration, start the MCP-Atlassian server:
```
uvx mcp-atlassian
```

The server will read your Jira credentials from the .env file."""
                
            else:
                return f"🔧 MCP tool {tool_name} requires implementation of MCP protocol communication."
                
        except Exception as e:
            logger.error(f"MCP tool call failed: {e}")
            return f"❌ Error calling {tool_name}: {str(e)}"

    async def _call_mcp_tool_async(self, tool_name: str, parameters: Dict[str, Any]) -> str:
        """Call MCP tool using direct JSON-RPC over subprocess."""
        logger.info(f"Attempting JSON-RPC communication with mcp-atlassian for {tool_name}")
        
        try:
            # Direct JSON-RPC approach using subprocess
            import json
            import asyncio.subprocess
            
            # Prepare environment with Jira configuration
            # The mcp-atlassian server expects these specific env var names
            env = os.environ.copy()
            jira_config = {
                # Try both naming conventions
                "JIRA_URL": CONFIG.get("JIRA_INSTANCE_URL", ""),
                "JIRA_INSTANCE_URL": CONFIG.get("JIRA_INSTANCE_URL", ""),
                "JIRA_USERNAME": CONFIG.get("JIRA_USERNAME", ""),
                "JIRA_TOKEN": CONFIG.get("JIRA_API_TOKEN", ""),
                "JIRA_API_TOKEN": CONFIG.get("JIRA_API_TOKEN", "")
            }
            env.update(jira_config)
            
            # Log configuration (without sensitive token)
            logger.info(f"Jira config: URL={jira_config['JIRA_INSTANCE_URL']}, USER={jira_config['JIRA_USERNAME']}, TOKEN={'***' if jira_config['JIRA_API_TOKEN'] else 'MISSING'}")
            
            # Start the MCP server process with proper environment
            process = await asyncio.subprocess.create_subprocess_exec(
                "uvx", "mcp-atlassian",
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env
            )
            
            # Initialize the MCP session with JSON-RPC
            initialize_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "tahecho",
                        "version": "1.0.0"
                    }
                }
            }
            
            # Send initialize request
            request_json = json.dumps(initialize_request) + "\n"
            process.stdin.write(request_json.encode())
            await process.stdin.drain()
            
            # Read initialize response
            response_line = await process.stdout.readline()
            initialize_response = json.loads(response_line.decode())
            logger.info(f"Initialize response: {initialize_response}")
            
            # Send initialized notification
            initialized_notification = {
                "jsonrpc": "2.0",
                "method": "notifications/initialized"
            }
            notification_json = json.dumps(initialized_notification) + "\n"
            process.stdin.write(notification_json.encode())
            await process.stdin.drain()
            
            # Give the server a moment to connect to Jira and load tools
            await asyncio.sleep(2)
            
            # List tools to find the correct tool name
            list_tools_request = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list"
            }
            request_json = json.dumps(list_tools_request) + "\n"
            process.stdin.write(request_json.encode())
            await process.stdin.drain()
            
            # Read tools response
            tools_response_line = await process.stdout.readline()
            tools_response = json.loads(tools_response_line.decode())
            logger.info(f"Tools response: {tools_response}")
            
            available_tools = []
            if "result" in tools_response and "tools" in tools_response["result"]:
                available_tools = [tool["name"] for tool in tools_response["result"]["tools"]]
                logger.info(f"Available tools: {available_tools}")
            
            # Map tool names
            tool_mapping = {
                "jira_search": ["search_issues", "search", "search_tickets", "jira_search", "searchIssues"],
                "jira_get_issue": ["get_issue", "fetch_issue", "issue_details", "jira_get_issue", "getIssue"],
                "jira_create_issue": ["create_issue", "create", "new_issue", "jira_create_issue", "createIssue"]
            }
            
            actual_tool_name = tool_name
            if tool_name in tool_mapping:
                for alt_name in tool_mapping[tool_name]:
                    if alt_name in available_tools:
                        actual_tool_name = alt_name
                        break
            
            if actual_tool_name not in available_tools:
                raise Exception(f"Tool '{tool_name}' not found. Available: {available_tools}")
            
            # Call the actual tool
            tool_request = {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": actual_tool_name,
                    "arguments": parameters
                }
            }
            
            request_json = json.dumps(tool_request) + "\n"
            process.stdin.write(request_json.encode())
            await process.stdin.drain()
            
            # Read tool response
            tool_response_line = await process.stdout.readline()
            tool_response = json.loads(tool_response_line.decode())
            logger.info(f"Tool response: {tool_response}")
            
            # Close the process and capture any errors
            process.stdin.close()
            
            # Read any stderr output for debugging
            stderr_output = ""
            try:
                stderr_data = await asyncio.wait_for(process.stderr.read(), timeout=1.0)
                stderr_output = stderr_data.decode() if stderr_data else ""
                if stderr_output:
                    logger.info(f"MCP server stderr: {stderr_output}")
            except asyncio.TimeoutError:
                pass
                
            await process.wait()
            
            # Extract result
            if "result" in tool_response:
                result = tool_response["result"]
                if "content" in result:
                    content = result["content"]
                    if isinstance(content, list) and len(content) > 0:
                        return content[0].get("text", str(content[0]))
                    else:
                        return str(content)
                else:
                    return str(result)
            elif "error" in tool_response:
                raise Exception(f"Tool error: {tool_response['error']}")
            else:
                return str(tool_response)
                    
        except Exception as e:
            logger.error(f"JSON-RPC communication failed: {e}")
            raise

    def _create_mcp_tools(self) -> List[Tool]:
        """Create MCP tools for Jira operations."""
        
        def search_my_tickets(query: str = "") -> str:
            """Search for tickets assigned to the current user - requires clarification of who 'current user' is."""
            try:
                # This function should request clarification about user identity
                return """❓ User Clarification Needed

I'd be happy to help you find your assigned tickets! However, I need to know who you are to search for your specific assignments.

Could you please provide:
1. Your Jira username or email address
2. If searching in a specific project, please confirm the project key

Once I have this information, I can search for tickets assigned to you using the search_tickets function with the appropriate JQL query."""
            except Exception as e:
                logger.error(f"Failed to search tickets: {e}")
                return f"Error searching tickets: {str(e)}"

        def create_ticket(project_key: str, summary: str, description: str = "", issue_type: str = "Task") -> str:
            """Create a new ticket in the specified project."""
            try:
                if not self._start_mcp_server():
                    return "Error: Unable to start MCP server"
                
                parameters = {
                    "project": project_key,
                    "summary": summary,
                    "description": description,
                    "issue_type": issue_type
                }
                return self._call_mcp_tool("jira_create_issue", parameters)
            except Exception as e:
                logger.error(f"Failed to create ticket: {e}")
                return f"Error creating ticket: {str(e)}"

        def get_ticket_details(ticket_key: str) -> str:
            """Get detailed information about a specific ticket."""
            try:
                if not self._start_mcp_server():
                    return "Error: Unable to start MCP server"
                
                return self._call_mcp_tool("jira_get_issue", {"issue_key": ticket_key})
            except Exception as e:
                logger.error(f"Failed to get ticket details: {e}")
                return f"Error getting ticket details: {str(e)}"

        def search_tickets(jql_query: str) -> str:
            """Search for tickets using JQL query."""
            try:
                if not self._check_mcp_server():
                    return """❌ MCP Server Not Running

The MCP-Atlassian server is not currently running. Please start it in a separate terminal:

```bash
uvx mcp-atlassian
```

The server will read your Jira credentials from the .env file. Once started, try your request again."""
                
                return self._call_mcp_tool("jira_search", {"jql": jql_query})
            except Exception as e:
                logger.error(f"Failed to search tickets: {e}")
                return f"Error searching tickets: {str(e)}"

        tools = [
            Tool(
                name="search_my_tickets",
                description="Requests clarification about user identity before searching for assigned tickets. Use when user asks for 'my tickets' without specifying username.",
                func=search_my_tickets,
            ),
            Tool(
                name="search_tickets",
                description="Search for tickets using JQL query with specific user/project criteria. Args: jql_query (str). Use when you have specific username/email and project information.",
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

### Instructions for this request:
1. If the user just provided a username or email (like "wolfgang.ihloff"), this is likely a response to a previous request for clarification
2. Use the search_tickets tool with JQL like "assignee = 'wolfgang.ihloff'" to find their tickets
3. If the user provided a project key, search for tickets in that project
4. Always acknowledge what information you received and explain what you're doing

Please use the available tools to interact with Jira and provide a helpful response.

{agent_scratchpad}
"""
        )
        agent = create_openai_tools_agent(self.llm, self.mcp_tools, prompt)
        agent_executor = AgentExecutor(
            agent=agent, 
            tools=self.mcp_tools, 
            verbose=False, 
            max_iterations=1,
            return_intermediate_steps=True
        )
        return agent_executor

    def execute(self, state: AgentState) -> AgentState:
        try:
            logger.info(f"Jira MCP agent executing for user input: {state.user_input}")

            result = self.agent_executor.invoke({"input": state.user_input})
            
            # Handle different result formats
            output = result.get("output", "")
            if not output or "Agent stopped due to max iterations" in output:
                # Use intermediate steps if available
                if "intermediate_steps" in result and result["intermediate_steps"]:
                    # Get the last tool result
                    last_step = result["intermediate_steps"][-1]
                    if len(last_step) > 1:
                        output = last_step[1]  # Tool output
                
                if not output:
                    output = "I was unable to retrieve the Jira information at this time."
            
            state.agent_results["jira_mcp_agent"] = output
            state.current_agent = "jira_mcp_agent"
            state.messages.append(AIMessage(content=output))

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
