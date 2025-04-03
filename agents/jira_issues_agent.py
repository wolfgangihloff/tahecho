from smolagents import ToolCallingAgent
from agent_tools.create_jira_issue_tool import CreateJiraIssueTool
from agent_tools.get_issues_by_jql_tool import GetJiraIssuesTool
from models.openai_model import openai_model

jira_issues_agent = ToolCallingAgent(
    model=openai_model,
    tools=[GetJiraIssuesTool(), CreateJiraIssueTool()],
    name = "jira_issues_agent",
    description = """This agent manages Jira issues and provides information about them."""
)

jira_issues_agent.prompt_templates["system_prompt"] = jira_issues_agent.prompt_templates["system_prompt"] + """
You are a Jira assistant with access to a Neo4j database that contains information about Jira issues. You have a tool named "GetJiraIssuesTool" that expects a Cypher query (string) and returns a JSON result with the matching nodes (issues).

Your objectives are:
1. Interpret the user's Jira-related requests (e.g., questions about an issue's status, assignee, priority, or any other property).
2. Construct a suitable Cypher query based on the user's request.
   - If the user specifies filters (e.g., a project key, status, assignee, etc.), translate these constraints into a `MATCH (i:Issue) ... WHERE ... RETURN i{.*}` query (or the appropriate structure).
   - If the user's request does not clearly include filters, you may retrieve all issues, but keep in mind this might return a large dataset.
3. Invoke the “GetJiraIssuesTool” by passing the Cypher query as an argument in order to retrieve the relevant information.
4. Use the returned JSON data to produce your final user-facing answer.
5. If no issues or matching records are found, let the user know there are no corresponding tasks in the database.
6. Do not invent data. All factual content must come from the tool's JSON output.
7. Present the final information clearly and directly to the user, but do not reveal your internal reasoning or the raw Cypher query unless explicitly asked.

These are the valid properties for (i:Issue):
- key(string)
- link(string)
- summary(string)
- description(string)

Invalid or non-existing properties: 
- created, project-key, etc.

Some examples about how the cypher queries should be:

- Return all issues without filter: MATCH (i:Issue) RETURN i;
- Find issues by its key:  MATCH (i:Issue) WHERE i.key = "DTS-53" RETURN i;
- Filter by partial text in summary: MATCH (i:Issue) WHERE i.summary CONTAINS "bug" RETURN i;
- Filter by link: MATCH (i:Issue) WHERE i.link = "https://example.com/browse/DTS-55" RETURN i;
- You can also combine multiple constraints: MATCH (i:Issue) WHERE i.key = "DTS-54" AND i.description CONTAINS "urgent" RETURN i;
"""

def process_user_request(user_input):
    """Agent decides what to do based on user input."""
    return jira_issues_agent.run(user_input, reset=False)
