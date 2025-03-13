from smolagents import ToolCallingAgent
from agents.jira_issues_agent import jira_issues_agent
from models.openai_model import openai_model

manager_agent = ToolCallingAgent(
    tools=[],
    model=openai_model,
    add_base_tools=False,
    managed_agents=[jira_issues_agent],

)

# Add name and description attributes manually since they're not accepted in the constructor
manager_agent.name = "manager_agent"
manager_agent.description = "Manages other agents and handles user requests."

def execute_multiagent(user_input):
    return manager_agent.run(user_input, reset=False)
