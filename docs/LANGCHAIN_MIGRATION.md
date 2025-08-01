# Migration from SmolAgents to LangChain/LangGraph

This document describes the migration of the Tahecho project from SmolAgents to LangChain and LangGraph for better multi-agent orchestration and tool calling capabilities.

## Overview

The migration replaces the SmolAgents-based multi-agent system with a more robust LangChain/LangGraph implementation that provides:

- **Better tool calling**: Native LangChain tool integration
- **State management**: Proper state persistence and conversation management
- **Workflow orchestration**: Clear state machine with conditional routing
- **Extensibility**: Easier to add new agents and tools
- **Debugging**: Better observability and error handling

## Architecture Changes

### Before (SmolAgents)
```
manager_agent (SmolAgents)
├── mcp_agent (SmolAgents)
└── graph_agent (SmolAgents)
```

### After (LangChain/LangGraph)
```
LangGraph Workflow
├── Task Classifier
├── Router
├── MCP Agent (LangChain)
├── Graph Agent (LangChain)
└── Final Response Generator
```

## New Components

### 1. State Management (`agents/state.py`)
- `AgentState`: Pydantic model for state management
- `create_initial_state()`: Helper function for state initialization
- Supports conversation persistence and metadata tracking

### 2. Task Classification (`agents/task_classifier.py`)
- `TaskClassifier`: Determines which agent should handle a request
- Uses LLM to classify tasks as "mcp", "graph", or "general"
- Provides reasoning for classification decisions

### 3. LangChain Agents
- `LangChainMCPAgent`: Handles direct Jira operations
- `LangChainGraphAgent`: Handles complex reasoning and relationships
- Both use LangChain's tool calling capabilities

### 4. Workflow Orchestration (`agents/langgraph_workflow.py`)
- `LangGraphWorkflow`: Main workflow using LangGraph
- State machine with conditional routing
- Memory persistence for conversations

### 5. Manager Agent (`agents/langchain_manager_agent.py`)
- `LangChainManagerAgent`: Entry point for the new system
- Maintains compatibility with existing app.py interface

## Key Benefits

### 1. Better Tool Integration
- Native LangChain tool decorators
- Automatic tool calling and response handling
- Better error handling for tool execution

### 2. State Persistence
- Conversation history maintained across sessions
- Thread-based conversation management
- Metadata tracking for debugging

### 3. Improved Routing
- LLM-based task classification
- Conditional workflow routing
- Clear separation of concerns

### 4. Extensibility
- Easy to add new agents
- Simple to modify workflow logic
- Better testing capabilities

## Migration Steps

### 1. Dependencies
Updated `requirements.txt`:
```diff
+ langchain==0.2.16
+ langchain-community==0.2.16
+ langchain-core==0.2.16
+ langgraph==0.2.16
- smolagents==1.14.0
```

### 2. File Structure
```
agents/
├── state.py                    # NEW: State management
├── task_classifier.py          # NEW: Task classification
├── langchain_mcp_agent.py      # NEW: MCP agent with LangChain
├── langchain_graph_agent.py    # NEW: Graph agent with LangChain
├── langgraph_workflow.py       # NEW: Main workflow
├── langchain_manager_agent.py  # NEW: Manager agent
├── manager_agent.py            # OLD: SmolAgents manager
├── mcp_agent.py               # OLD: SmolAgents MCP agent
└── graph_agent.py             # OLD: SmolAgents graph agent
```

### 3. App Integration
Updated `app.py`:
```python
# OLD
from agents.manager_agent import execute_multiagent
response = await execute_multiagent(message.content)

# NEW
from agents.langchain_manager_agent import langchain_manager_agent
response = langchain_manager_agent.run(message.content, conversation_id=conversation_id)
```

## Testing

Run the test script to verify the migration:
```bash
python tests/integration/test_langchain_implementation.py
```

This will test:
- State management
- Task classification
- Manager agent execution

## Configuration

The new implementation uses the same configuration as before:
- `config.py`: OpenAI API settings
- Environment variables: Jira credentials
- Docker Compose: Service configuration

## Backward Compatibility

The new implementation maintains the same external interface:
- Same function signatures
- Same response format
- Same error handling patterns

## Future Enhancements

With LangChain/LangGraph, we can easily add:

1. **New Agents**: Add specialized agents for different tasks
2. **Advanced Routing**: Implement more sophisticated routing logic
3. **Memory Management**: Add conversation memory and context
4. **Observability**: Better logging and monitoring
5. **Testing**: Unit tests for individual components

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all LangChain dependencies are installed
2. **Tool Calling**: Verify MCP server is running and accessible
3. **State Persistence**: Check conversation ID generation
4. **Memory Issues**: Monitor LangGraph memory usage

### Debug Mode

Enable verbose logging in agents:
```python
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
```

## Performance Considerations

- LangGraph adds some overhead for state management
- Tool calling is more robust but slightly slower
- Memory usage increases with conversation history
- Consider implementing conversation cleanup for long-running sessions

## Conclusion

The migration to LangChain/LangGraph provides a more robust, maintainable, and extensible foundation for the Tahecho multi-agent system. The improved tool calling, state management, and workflow orchestration make it easier to add new features and maintain the codebase. 