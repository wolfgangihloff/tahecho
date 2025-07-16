from typing import Dict, Any, TypedDict, Annotated, Optional
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import MemorySaver
from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate
from config import CONFIG

from agents.state import AgentState, create_initial_state
from agents.task_classifier import task_classifier
from agents.langchain_mcp_agent import langchain_mcp_agent
from agents.langchain_graph_agent import langchain_graph_agent


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
        from agents.task_classifier import TaskClassifier
        classifier = TaskClassifier()
        return classifier.classify_task(state)
    
    def _route_to_agent(self, state: AgentState) -> AgentState:
        """Route to the appropriate agent based on task classification."""
        # This node just passes through the state
        # The routing logic is handled by the conditional edges
        return state
    
    def _execute_mcp_agent(self, state: AgentState) -> AgentState:
        """Execute the MCP agent for direct Jira operations."""
        return langchain_mcp_agent.execute(state)
    
    def _execute_graph_agent(self, state: AgentState) -> AgentState:
        """Execute the Graph agent for complex reasoning."""
        return langchain_graph_agent.execute(state)
    
    def _generate_final_response(self, state: AgentState) -> AgentState:
        """Generate the final response based on agent results."""
        try:
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
            # Fallback response
            fallback_response = f"I apologize, but I encountered an error while processing your request: {str(e)}"
            state.final_answer = fallback_response
            state.messages.append(AIMessage(content=fallback_response))
            return state
    
    def _should_continue(self, state: AgentState) -> str:
        """Determine the next step in the workflow."""
        if state.task_type == "mcp":
            return "mcp"
        elif state.task_type == "graph":
            return "graph"
        elif state.task_type == "general":
            return "general"
        else:
            return "end"
    
    def execute(self, user_input: str, conversation_id: Optional[str] = None) -> str:
        """Execute the workflow with the given user input."""
        try:
            # Create initial state
            initial_state = create_initial_state(user_input, conversation_id)
            
            # Execute the workflow
            config = {"configurable": {"thread_id": conversation_id or "default"}}
            result = self.app.invoke(initial_state, config)
            
            # Return the final answer
            return result.final_answer or "No response generated."
            
        except Exception as e:
            return f"Workflow execution failed: {str(e)}"


# Global instance
langgraph_workflow = LangGraphWorkflow() 