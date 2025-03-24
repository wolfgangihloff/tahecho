from smolagents import ToolCallingAgent
from agent_tools.create_jira_issue_tool import CreateJiraIssueTool
from agent_tools.get_issues_by_jql_tool import GetIssuesByJQLTool
from agent_tools.get_jira_issues_tool import GetJiraIssuesTool
from models.openai_model import openai_model

jira_issues_agent = ToolCallingAgent(
    model=openai_model,
    tools=[GetIssuesByJQLTool(), CreateJiraIssueTool()],
    name = "jira_issues_agent",
    description = """This agent manages Jira issues and provides information about them."""
)

jira_issues_agent.prompt_templates["system_prompt"] = jira_issues_agent.prompt_templates["system_prompt"] + """
                       
IMPORTANT: You must ALWAYS return the COMPLETE list of issues that match the query, with ALL their details.
- NEVER summarize the results
- NEVER provide just a sample or example of the issues
- NEVER explain what the issues are instead of showing them
- NEVER truncate the list of issues unless absolutely necessary due to token limits

Process:
1. Generate a JQL query based on the user's input (if no specific criteria are provided, use a query for issues from the last 7 days). You should
also generate a maxResult number, which will be the number of results the API will return, if not specified in the user's input then it should be
by default 50.
2. Execute the query using the jqlRequestIssuesTool
3. Return ALL issues with ALL their information using the FinalAnswerIssuesTool
4. If and ONLY if the response exceeds token limits, include as many complete issues as possible and add this exact message at the end: 
   "Note: There are additional issues matching these criteria that cannot be displayed due to token limitations."

Remember: Your primary responsibility is to show the COMPLETE data for ALL matching issues. Do not attempt to be helpful by summarizing or condensing the information.
If the content or quantity of issues is too big just add as many as possible and clarify at the end of the response that there are more issues
matching the query but you couldn't fit them all in the single response
                       """

def process_user_request(user_input):
    """Agent decides what to do based on user input."""
    return jira_issues_agent.run(user_input, reset=False)
