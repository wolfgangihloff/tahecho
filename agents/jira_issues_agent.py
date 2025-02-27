from smolagents.agents import ToolCallingAgent
from agent_tools.create_jira_issue_tool import createJiraIssueTool
from config import CONFIG
from models.openai_model import openai_model
from tools import getAllJiraIssuesTool
from smolagents import OpenAIServerModel

get_all_jira_issues_tool=getAllJiraIssuesTool()
create_jira_issue_tool=createJiraIssueTool()


jira_issues_agent = ToolCallingAgent(
    model=OpenAIServerModel(
        model_id="gpt-4o",
        api_key=CONFIG["OPENAI_API_KEY"]
        ),
        tools=[get_all_jira_issues_tool, create_jira_issue_tool],
        add_base_tools=False
)

def process_user_request(user_input):
    """Agent decides what to do based on user input."""
    return jira_issues_agent.run(user_input, reset=False)