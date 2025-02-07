from config import CONFIG
from smolagents import OpenAIServerModel
from smolagents.agents import CodeAgent
from tools import get_my_jira_issues


agent = CodeAgent(
    model=OpenAIServerModel(
        model_id="gpt-4o",
        api_key=CONFIG["OPENAI_API_KEY"]
        ),
        tools=[get_my_jira_issues]
)

def process_user_request(user_input):
    """Agent decides what to do based on user input."""
    return agent.run(user_input)