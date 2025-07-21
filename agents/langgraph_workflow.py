from typing import Dict, Any, TypedDict, Annotated, Optional
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import MemorySaver
from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate
from config import CONFIG
import logging
import re

from agents.state import AgentState, create_initial_state
from agents.task_classifier import task_classifier
from agents.langchain_mcp_agent import langchain_mcp_agent
from agents.langchain_graph_agent import langchain_graph_agent

logger = logging.getLogger(__name__)


class LangGraphWorkflow:
    """Main workflow using LangGraph to orchestrate the multi-agent system."""
    
    def __init__(self):
        self.llm = init_chat_model(
            CONFIG["OPENAI_SETTINGS"]["model"], 
            model_provider="openai",
            temperature=0.1
        )
        
        # Create the graph
        self.workflow = self._create_workflow()
        
        # Create memory saver for conversation persistence
        self.memory = MemorySaver()
        
        # Compile the graph
        self.app = self.workflow.compile(checkpointer=self.memory)
    
    def _create_workflow(self) -> StateGraph:
        """Create the LangGraph workflow."""
        
        # Create the state graph
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("classify_task", self._classify_task)
        workflow.add_node("route_to_agent", self._route_to_agent)
        workflow.add_node("execute_mcp_agent", self._execute_mcp_agent)
        workflow.add_node("execute_graph_agent", self._execute_graph_agent)
        workflow.add_node("generate_final_response", self._generate_final_response)
        
        # Add edges
        workflow.add_edge(START, "classify_task")
        workflow.add_edge("classify_task", "route_to_agent")
        workflow.add_conditional_edges(
            "route_to_agent",
            self._should_continue,
            {
                "mcp": "execute_mcp_agent",
                "graph": "execute_graph_agent",
                "general": "generate_final_response",
                "end": END
            }
        )
        workflow.add_edge("execute_mcp_agent", "generate_final_response")
        workflow.add_edge("execute_graph_agent", "generate_final_response")
        workflow.add_edge("generate_final_response", END)
        
        return workflow
    
    def _classify_task(self, state: AgentState) -> AgentState:
        """Classify the task to determine which agent should handle it."""
        try:
            from agents.task_classifier import TaskClassifier
            classifier = TaskClassifier()
            return classifier.classify_task(state)
        except Exception as e:
            logger.error(f"Task classification failed: {e}")
            state.task_type = "general"
            return state
    
    def _route_to_agent(self, state: AgentState) -> AgentState:
        """Route to the appropriate agent based on task classification."""
        # This node just passes through the state
        # The routing logic is handled by the conditional edges
        return state
    
    def _execute_mcp_agent(self, state: AgentState) -> AgentState:
        """Execute the MCP agent for direct Jira operations."""
        try:
            return langchain_mcp_agent.execute(state)
        except Exception as e:
            logger.error(f"MCP agent execution failed: {e}")
            state.agent_results["mcp_agent"] = f"Error: {str(e)}"
            return state
    
    def _execute_graph_agent(self, state: AgentState) -> AgentState:
        """Execute the Graph agent for complex reasoning."""
        try:
            return langchain_graph_agent.execute(state)
        except Exception as e:
            logger.error(f"Graph agent execution failed: {e}")
            state.agent_results["graph_agent"] = f"Error: {str(e)}"
            return state
    
    def _generate_final_response(self, state: AgentState) -> AgentState:
        """Generate the final response based on agent results."""
        try:
            # Check if we have agent errors first
            agent_errors = []
            for agent, result in state.agent_results.items():
                if isinstance(result, str) and result.startswith("Error:"):
                    agent_errors.append((agent, result))
            
            if agent_errors:
                # Log detailed errors for debugging
                for agent, error in agent_errors:
                    logger.error(f"{agent} failed: {error}")
                
                # Generate user-friendly error message
                user_message = self._create_user_friendly_error_message(agent_errors, state.user_input)
                state.final_answer = user_message
                state.messages.append(AIMessage(content=user_message))
                return state
            
            # Create a prompt for generating the final response
            final_prompt = ChatPromptTemplate.from_template("""
You are the final response generator for a Jira management system. Your job is to create a clear, user-friendly response based on the agent results.

User's original request: {user_input}

Agent results:
{agent_results}

Current agent: {current_agent}

Please generate a final response that:
1. Directly answers the user's question
2. Uses the agent results as the source of truth
3. Presents the information in a clear, natural way
4. Doesn't mention internal agent names or technical details
5. Is helpful and actionable

Final response:
""")
            
            # Create the chain
            chain = final_prompt | self.llm
            
            # Format agent results
            agent_results_text = "\n".join([
                f"- {agent}: {result}" 
                for agent, result in state.agent_results.items()
            ]) if state.agent_results else "No specific agent results available."
            
            # Generate final response
            result = chain.invoke({
                "user_input": state.user_input,
                "agent_results": agent_results_text,
                "current_agent": state.current_agent or "none"
            })
            
            # Update state
            state.final_answer = result.content
            state.messages.append(AIMessage(content=result.content))
            
            return state
            
        except Exception as e:
            logger.error(f"Final response generation failed: {e}")
            # Fallback response
            fallback_response = self._create_user_friendly_error_message([("system", str(e))], state.user_input)
            state.final_answer = fallback_response
            state.messages.append(AIMessage(content=fallback_response))
            return state
    
    def _create_user_friendly_error_message(self, agent_errors: list, user_input: str) -> str:
        """Create a user-friendly error message based on the type of error."""
        if not agent_errors:
            return "I'm sorry, but I encountered an unexpected issue. Please try again."
        
        # Analyze the errors to determine what went wrong
        error_types = []
        for agent, error in agent_errors:
            error_str = str(error).lower()
            
            # Check for specific error types
            if "api key" in error_str or "invalid api key" in error_str:
                error_types.append("openai_api")
            elif "401" in error_str or "unauthorized" in error_str:
                if "jira" in error_str or agent == "mcp_agent":
                    error_types.append("jira_auth")
                else:
                    error_types.append("api_auth")
            elif "connection" in error_str or "timeout" in error_str:
                error_types.append("connection")
            elif "neo4j" in error_str or "graph" in error_str:
                error_types.append("graph_db")
            else:
                error_types.append("general")
        
        # Create appropriate user message
        if "openai_api" in error_types:
            return "I'm having trouble connecting to my language processing service. This might be a temporary issue. Please try again in a moment."
        elif "jira_auth" in error_types:
            return "I'm unable to access your Jira information right now. Please check your Jira credentials and try again."
        elif "graph_db" in error_types:
            return "I'm having trouble accessing the relationship database. You can still ask basic questions about your tasks."
        elif "connection" in error_types:
            return "I'm experiencing connection issues with one of my services. Please try again in a moment."
        elif "api_auth" in error_types:
            return "I'm having trouble authenticating with one of my services. Please check your configuration and try again."
        else:
            return "I encountered an issue while processing your request. Please try rephrasing your question or try again later."
    
    def _should_continue(self, state: AgentState) -> str:
        """Determine the next step in the workflow."""
        try:
            if state.task_type == "mcp":
                return "mcp"
            elif state.task_type == "graph":
                return "graph"
            elif state.task_type == "general":
                return "general"
            else:
                return "end"
        except Exception as e:
            logger.error(f"Routing decision failed: {e}")
            return "general"
    
    def execute(self, user_input: str, conversation_id: Optional[str] = None) -> str:
        """Execute the workflow with the given user input."""
        try:
            # Create initial state
            initial_state = create_initial_state(user_input, conversation_id)
            
            # Execute the workflow
            config = {"configurable": {"thread_id": conversation_id or "default"}}
            result = self.app.invoke(initial_state, config)
            
            # Handle different result types
            if hasattr(result, 'final_answer'):
                return result.final_answer or "No response generated."
            elif isinstance(result, dict) and 'final_answer' in result:
                return result['final_answer'] or "No response generated."
            elif isinstance(result, AgentState):
                return result.final_answer or "No response generated."
            else:
                # Try to extract final_answer from the result object
                logger.warning(f"Unexpected result type: {type(result)}")
                logger.warning(f"Result attributes: {dir(result)}")
                
                # Try different ways to access the final answer
                if hasattr(result, 'get'):
                    final_answer = result.get('final_answer')
                    if final_answer:
                        return final_answer
                
                # If all else fails, return a helpful error message
                return f"I'm sorry, but I encountered an issue processing your request. Please try again or rephrase your question."
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            return f"I'm sorry, but I encountered an unexpected issue. Please try again."


# Global instance
langgraph_workflow = LangGraphWorkflow() 