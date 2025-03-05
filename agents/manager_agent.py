from smolagents.agents import CodeAgent
from agents import jira_issues_agent
from models import openai_model

manager_agent = CodeAgent(
    tools=[],
    model=openai_model,
    managed_agents=[jira_issues_agent]
)

def execute_multiagent(user_input):
    return manager_agent.run(user_input, reset=False)