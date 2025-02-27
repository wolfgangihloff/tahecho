from smolagents.agents import ToolCallingAgent
from agent_tools.create_jira_issue_tool import CreateJiraIssueTool
from agent_tools.get_jira_issues_tool import GetJiraIssuesTool
from models.openai_model import openai_model

get_all_jira_issues_tool=GetJiraIssuesTool()
create_jira_issue_tool=CreateJiraIssueTool()

jira_issues_agent = ToolCallingAgent(
    model=openai_model,
        tools=[get_all_jira_issues_tool, create_jira_issue_tool],
        add_base_tools=False
)

def process_user_request(user_input):
    """Agent decides what to do based on user input."""
    return jira_issues_agent.run(user_input, reset=False)