from smolagents.agents import CodeAgent, ToolCallingAgent

get_all_jira_issues_tool = GetAllJiraIssuesTool()

jira_issues_agent = ToolCallingAgent(
    model=openai_model,
    tools=[get_all_jira_issues_tool],
    add_base_tools=False,
)

manager_agent = CodeAgent(
    tools=[],
    model=openai_model,
    managed_agents=[jira_issues_agent]
)

def execute_multiagent(user_input):
    return manager_agent.run(user_input, reset=False)