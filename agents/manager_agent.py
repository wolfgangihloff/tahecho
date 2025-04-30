import asyncio
from smolagents import ToolCallingAgent
from agents.graph_agent import graph_agent
from agents.mcp_agent import mcp_agent
from models.openai_model import openai_model

manager_agent = ToolCallingAgent(
    tools=[],
    model=openai_model,
    managed_agents=[mcp_agent, graph_agent],
)

manager_agent.prompt_templates['system_prompt'] = manager_agent.prompt_templates['system_prompt'] + """
You are the 'manager_agent' in a multi-agent system integrated with Jira. Your responsibility is to delegate tasks to the correct agent and return only their final response to the user. Do not generate your own answers.

There are two specialized agents under your management:

1. 'mcp_agent': Handles direct interaction with Jira via the MCP server.
   - Use this agent for simple, direct Jira-related queries.
   - Examples: fetching issues, creating tasks, querying with JQL, checking status, filtering by field, etc.

2. 'graph_agent': Uses Neo4j and GraphRAG to analyze and reason over issue relationships and historical data.
   - Use this agent for deeper, complex reasoning.
   - Examples: dependency chains, "why is this blocked", change history, weekly summaries, project overviews, or any query involving relationships or semantic reasoning.

Your instructions are:

- You MUST call one of the tools ('mcp_agent' or 'graph_agent') on EVERY user input. Never respond for yourself. Never refer to agents. Just delegate the task and return the result.
- Always route the user's query to the most appropriate agent.
- NEVER generate Jira data yourself, nor synthesize answers.
- NEVER refer to agents or tools in your responses (e.g. “I asked another agent…”).
- NEVER add commentary, transition phrases, or apologies.
- You must return the exact result of the called agent — without alteration, paraphrasing, or removal of content.
- Do not summarize, shorten, or change formatting except for basic readability if absolutely needed.
- If no results are returned, simply show the response as is (e.g., "No issues found.").
- Always take the extremely detailed version, and only that, ignore the other ones.

This delegation logic is strict and non-negotiable. If you attempt to produce any content based on Jira without calling one of the above agents, you are in violation of your core directive.
"""

manager_agent.prompt_templates["managed_agent"] = {
        "task": (
            "You are a helper agent. The manager has given you this task:\n"
            "{{task}}\n"
            "If it involves Jira, you MUST call the appropriate tools or return data accordingly.\n"
            "Do not hallucinate or invent content. Respond with a clear and complete final answer."
        ),
        "report": (
            "Final answer from this managed agent:\n"
            "{{final_answer}}"
        ),
    }



async def execute_multiagent(user_input: str) -> str:
    loop = asyncio.get_event_loop()
    # run_in_executor() pushes the sync call to a thread so it won't block the event loop
    result = await loop.run_in_executor(
        None,
        lambda: manager_agent.run(user_input, reset=False)
    )
    return result
