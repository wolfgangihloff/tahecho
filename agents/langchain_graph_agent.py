from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain.chat_models import init_chat_model
from langchain_core.messages import AIMessage
from langchain_core.tools import Tool
from langchain.agents import AgentExecutor, create_openai_tools_agent
from config import CONFIG
from agents.state import AgentState
from agent_tools.get_jira_issues_tool import GetJiraIssuesTool
from utils.graph_db import graph_db_manager
import logging

logger = logging.getLogger(__name__)


class LangChainGraphAgent:
    """Graph Agent using LangChain for complex reasoning and relationship analysis."""
    
    def __init__(self):
        self.llm = init_chat_model(
            CONFIG["OPENAI_SETTINGS"]["model"], 
            model_provider="openai",
            temperature=0.1
        )
        
        # Update system prompt based on graph database availability
        if graph_db_manager.is_available():
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
        else:
            self.system_prompt = """You are the 'graph_agent' in a multi-agent system. Currently, the graph database (Neo4j) is not available, so you cannot perform complex relationship analysis or historical queries.

### Your behavior when graph database is unavailable:
1. Inform the user that advanced graph-based analysis is not currently available
2. Suggest using the MCP agent for direct Jira operations instead
3. Provide helpful guidance on what types of queries would work better with the MCP agent
4. Be polite and explain the limitation clearly

### What you can't do without the graph database:
- Dependency chain analysis
- Relationship queries between issues
- Historical change analysis
- Complex reasoning across multiple issues
- Semantic search for similar tasks

### What the user should do instead:
- Use the MCP agent for direct Jira operations
- Query specific issues by key or status
- Get current issue information
- Perform basic Jira management tasks
"""
        
        self.langchain_tools = self._create_graph_tools()
        self.agent_executor = self._create_agent()
    
    def _create_graph_tools(self):
        tools = []
        
        if graph_db_manager.is_available():
            # Only add graph tools if database is available
            def run_cypher_query(query: str) -> str:
                try:
                    return GetJiraIssuesTool.invoke(query)
                except Exception as e:
                    logger.error(f"Cypher query execution failed: {e}")
                    raise
            
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
            logger.info(f"Graph agent executing for user input: {state.user_input}")
            
            if not graph_db_manager.is_available():
                # Provide a helpful response when graph database is not available
                response = """I notice you're asking for complex analysis that requires the graph database, but Neo4j is not currently available. 

For this type of query, I recommend using the MCP agent instead, which can directly access Jira and provide current information about issues, status updates, and basic task management.

Would you like me to redirect your request to the MCP agent, or would you prefer to ask a different type of question that doesn't require relationship analysis?"""
                
                logger.info("Graph agent provided fallback response due to unavailable graph database")
                state.agent_results["graph_agent"] = response
                state.current_agent = "graph_agent"
                state.messages.append(AIMessage(content=response))
                return state
            
            # Normal execution when graph database is available
            result = self.agent_executor.invoke({"input": state.user_input})
            state.agent_results["graph_agent"] = result["output"]
            state.current_agent = "graph_agent"
            state.messages.append(AIMessage(content=result["output"]))
            
            logger.info("Graph agent execution completed successfully")
            return state
            
        except Exception as e:
            logger.error(f"Graph agent execution failed: {e}")
            
            # Create a user-friendly error message
            error_message = self._create_user_friendly_error_message(str(e))
            
            state.agent_results["graph_agent"] = f"Error: {str(e)}"
            state.current_agent = "graph_agent"
            state.messages.append(AIMessage(content=error_message))
            
            return state
    
    def _create_user_friendly_error_message(self, error: str) -> str:
        """Create a user-friendly error message based on the error type."""
        error_lower = error.lower()
        
        if "neo4j" in error_lower or "graph" in error_lower:
            return "I'm having trouble accessing the relationship database. You can still ask basic questions about your tasks using the MCP agent."
        elif "connection" in error_lower or "timeout" in error_lower:
            return "I'm experiencing connection issues with the relationship database. Please try again in a moment."
        elif "cypher" in error_lower or "query" in error_lower:
            return "I encountered an issue while analyzing the relationships. Please try rephrasing your question."
        elif "invalid api key" in error_lower or "api key" in error_lower:
            return "I'm having trouble connecting to my language processing service. This might be a temporary issue. Please try again in a moment."
        else:
            return "I encountered an issue while analyzing the relationships. Please try asking a different question or use the MCP agent for direct Jira operations."


langchain_graph_agent = LangChainGraphAgent() 