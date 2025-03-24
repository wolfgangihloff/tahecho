from smolagents import ToolCallingAgent
from models.openai_model import openai_model

jql_query_agent = ToolCallingAgent(
    model=openai_model,
    tools=[],
    add_base_tools=False,
)

jql_query_agent.name = "jql_query_agent"
jql_query_agent.description = """
    Generates JQL queries based on natural language descriptions. The purpose of this agent is to generate jql queries,
    that will be used in the jira_issues_agent to get the specified issues. The agent will receive a message that gives information
    about how the user wants anything related with Jira issues, based on that the agent will generate as a response a jql query
    for that input. The agent only needs to return nothing more than the jql query, if there is no specifications defined assume
    a basic jql query of all tasks in the last 30 days.
    
    Examples:
    
    1. Input: "Show me all open bugs assigned to me"
       Output: issuetype = Bug AND status = "Open" AND assignee = currentUser()
    
    2. Input: "Find all high priority tasks that are finished"
       Output: issuetype = Task AND priority = High AND status = "Done"
    
    3. Input: "Show tasks created this week"
       Output: issuetype = Task AND created >= startOfWeek()
    
    4. Input: "Find all unassigned issues in the project"
       Output: assignee is EMPTY AND project = currentProject()
    
    5. Input: "Show me issues updated yesterday with high priority"
       Output: updated >= startOfDay(-1) AND updated <= endOfDay(-1) AND priority = High
    
    6. Input: "Tasks that are already finished"
       Output: issuetype = Task AND status = "Done"
    
    7. Input: "Bugs that need to be fixed urgently"
       Output: issuetype = Bug AND priority = Highest
    
    8. Input: "Work items I need to do today"
       Output: assignee = currentUser() AND status != "Done" AND status != "Closed"
    """
