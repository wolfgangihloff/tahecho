from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain.chat_models import init_chat_model
from langchain_core.messages import AIMessage
from langchain_core.tools import Tool
from langchain.agents import AgentExecutor, create_openai_tools_agent
from config import CONFIG
from agents.state import AgentState
from agent_tools.get_jira_issues_tool import GetJiraIssuesTool


class LangChainGraphAgent:
    """Graph Agent using LangChain for complex reasoning and relationship analysis."""
    
    def __init__(self):
        self.llm = init_chat_model(
            CONFIG["OPENAI_SETTINGS"]["model"], 
            model_provider="openai",
            temperature=0.1
        )
        self.system_prompt = """You are the 'graph_agent' in a multi-agent system. Your job is to answer complex Jira-related questions using a graph database (Neo4j) and a semantic reasoning system (GraphRAG). The graph contains Jira issues, their relationships (e.g., dependencies, blockers), and change history (changelogs).

You are not connected to Jira directly. Instead, you reason over structured data extracted into a graph. You must use this graph to answer questions that involve:
- Dependency chains (e.g., "Why is this task blocked?")
- Relationship queries (e.g., "Which tasks are dependent on X?")
- Historical analysis (e.g., "What changed this week?")
- Contextual summaries across multiple issues
- Semantic search for similar tasks
- Any reasoning based on structure or history, not just fields

### Your behavior:
1. Use the GraphRAG retriever to semantically match the user's query with relevant issues and relationships.
2. When the query involves timeline or change tracking, query `:ChangeEvent` nodes connected via `[:HAS_CHANGE]`.
3. When the query involves dependency or blocking relationships, traverse `[:BLOCKS]` relationships between issues.
4. Do not hallucinate or guess data. Use only what exists in the graph.
5. Do not reference "graph", "cypher", "database", or "tool" in the answer. The user must receive natural, informative output.
6. Do not perform direct Jira actions or JQL queries — delegate that to the 'mcp_agent'.
"""
        self.langchain_tools = self._create_graph_tools()
        self.agent_executor = self._create_agent()
    
    def _create_graph_tools(self):
        tools = []
        graph_tool = GetJiraIssuesTool  # Use the instance, not a constructor
        def run_cypher_query(query: str) -> str:
            try:
                return graph_tool.invoke(query)
            except Exception as e:
                return f"Error running Cypher query: {str(e)}"
        tools.append(Tool(
            name="run_cypher_query",
            description="Run a Cypher query against the Neo4j Jira graph database.",
            func=run_cypher_query
        ))
        return tools
    
    def _create_agent(self):
        prompt = ChatPromptTemplate.from_template(self.system_prompt + """
User request: {input}
Please use the available tools to query the graph database and provide a comprehensive answer.

{agent_scratchpad}
""")
        agent = create_openai_tools_agent(self.llm, self.langchain_tools, prompt)
        agent_executor = AgentExecutor(agent=agent, tools=self.langchain_tools, verbose=False)
        return agent_executor
    
    def execute(self, state: AgentState) -> AgentState:
        try:
            result = self.agent_executor.invoke({"input": state.user_input})
            state.agent_results["graph_agent"] = result["output"]
            state.current_agent = "graph_agent"
            state.messages.append(AIMessage(content=result["output"]))
            return state
        except Exception as e:
            error_msg = f"Graph Agent execution failed: {str(e)}"
            state.agent_results["graph_agent"] = error_msg
            state.current_agent = "graph_agent"
            state.messages.append(AIMessage(content=error_msg))
            return state

langchain_graph_agent = LangChainGraphAgent() 