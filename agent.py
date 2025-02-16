from config import CONFIG
from smolagents import OpenAIServerModel
from smolagents.agents import ToolCallingAgent
from tools import createJiraIssueTool, get_finished_issues, get_my_jira_issues

create_jira_issue_tool=createJiraIssueTool()

agent = ToolCallingAgent(
    model=OpenAIServerModel(
        model_id="gpt-4o",
        api_key=CONFIG["OPENAI_API_KEY"]
        ),
        tools=[get_my_jira_issues, get_finished_issues, create_jira_issue_tool],
        add_base_tools=False
)

def process_user_request(user_input):
    """Agent decides what to do based on user input."""
    return agent.run(user_input)