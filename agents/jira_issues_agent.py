from smolagents import ToolCallingAgent
from agent_tools.create_jira_issue_tool import CreateJiraIssueTool
from agent_tools.get_issues_by_jql_tool import GetJiraIssuesTool
from models.openai_model import openai_model
from smolagents.mcp_client import MCPClient

mcp_client = MCPClient({"url": "http://mcp:8002/sse"})
jira_tool = mcp_client.get_tools()

jira_issues_agent = ToolCallingAgent(
    model=openai_model,
    tools=jira_tool,
    name = "jira_issues_agent",
    description = """This agent manages Jira issues and provides information about them."""
)

jira_issues_agent.prompt_templates["system_prompt"] = jira_issues_agent.prompt_templates["system_prompt"] + """
You are a Jira assistant with access to an MCP server of atlassian that allows you to do any type of action related to Jira.
"""

def process_user_request(user_input):
    """Agent decides what to do based on user input."""
    return jira_issues_agent.run(user_input, reset=False)
