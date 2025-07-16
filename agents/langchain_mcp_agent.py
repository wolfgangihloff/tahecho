from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain.chat_models import init_chat_model
from langchain_core.messages import AIMessage
from langchain_core.tools import Tool
from langchain.agents import AgentExecutor, create_openai_tools_agent
from config import CONFIG
from agents.state import AgentState
from jira_integration.jira_client import jira_client

class LangChainMCPAgent:
    """MCP Agent using LangChain for direct Jira operations."""
    
    def __init__(self):
        self.llm = init_chat_model(
            CONFIG["OPENAI_SETTINGS"]["model"], 
            model_provider="openai",
            temperature=0.1
        )
        
        self.system_prompt = """You are the 'mcp_agent' in a multi-agent system. You are directly connected to a Jira MCP server, which allows you to perform real-time operations with Jira via tools provided through MCP.

Your purpose is to handle all direct Jira actions and queries that do not require complex graph reasoning or historical dependency analysis.

### Your capabilities:
You have access to a set of tools exposed by the Jira MCP server. These tools allow you to:
- Retrieve issues using JQL
- Filter issues by project, assignee, status, priority, labels, etc.
- Get issue details (summary, status, description, etc.)
- Create new issues
- Update issue fields
- Change issue status or assign users

### Your behavior:
1. You must ALWAYS use tools to perform any Jira-related request.
2. You must NEVER generate, guess, or hallucinate issue data.
3. You are NOT allowed to summarize or paraphrase the returned data — show it as-is.
4. You must NEVER mention that you are calling a tool or server. The user must see only the final answer.
5. If no data is returned, say exactly what the tool says (e.g., "No matching issues found.")
6. You do not have access to changelogs, graphs, dependencies, or advanced semantic summaries — delegate those to the appropriate agent (not you).
7. If you get an error trying an action on the mcp server you should rewrite the query in the next steps until you manage to get it done.

### Output expectations:
- Display issue data exactly as it comes from the tools.
- Format dates or links only if needed for clarity.
- Never hide or omit issue entries, even if the result contains dozens of issues.

Do not explain what you are doing. Just call the tools and return the result clearly.
"""
        self.langchain_tools = self._create_jira_tools()
        self.agent_executor = self._create_agent()
    
    def _create_jira_tools(self):
        tools = []
        
        def get_jira_issues(jql: str) -> str:
            """Retrieve Jira issues using a JQL query."""
            try:
                result = jira_client.instance.jql(jql, limit=50)
                return str(result)
            except Exception as e:
                return f"Error retrieving issues: {str(e)}"
        tools.append(Tool(
            name="get_jira_issues",
            description="Retrieve Jira issues using a JQL query.",
            func=get_jira_issues
        ))
        
        def create_jira_issue(project_key: str, summary: str, issue_type: str, description: str = "") -> str:
            """Create a new Jira issue."""
            try:
                result = jira_client.instance.issue_create({
                    "project": project_key,
                    "summary": summary,
                    "issuetype": {"name": issue_type},
                    "description": description
                })
                return str(result)
            except Exception as e:
                return f"Error creating issue: {str(e)}"
        tools.append(Tool(
            name="create_jira_issue",
            description="Create a new Jira issue.",
            func=create_jira_issue
        ))
        
        def update_jira_issue(issue_key: str, field: str, value: str) -> str:
            """Update a field of an existing Jira issue."""
            try:
                result = jira_client.instance.issue_update(issue_key, fields={field: value})
                return str(result)
            except Exception as e:
                return f"Error updating issue: {str(e)}"
        tools.append(Tool(
            name="update_jira_issue",
            description="Update a field of an existing Jira issue.",
            func=update_jira_issue
        ))
        
        return tools
    
    def _create_agent(self):
        prompt = ChatPromptTemplate.from_template(self.system_prompt + """
User request: {input}
Please use the available tools to fulfill the user's request.

{agent_scratchpad}
""")
        agent = create_openai_tools_agent(self.llm, self.langchain_tools, prompt)
        agent_executor = AgentExecutor(agent=agent, tools=self.langchain_tools, verbose=False)
        return agent_executor
    
    def execute(self, state: AgentState) -> AgentState:
        try:
            result = self.agent_executor.invoke({"input": state.user_input})
            state.agent_results["mcp_agent"] = result["output"]
            state.current_agent = "mcp_agent"
            state.messages.append(AIMessage(content=result["output"]))
            return state
        except Exception as e:
            error_msg = f"MCP Agent execution failed: {str(e)}"
            state.agent_results["mcp_agent"] = error_msg
            state.current_agent = "mcp_agent"
            state.messages.append(AIMessage(content=error_msg))
            return state

langchain_mcp_agent = LangChainMCPAgent() 