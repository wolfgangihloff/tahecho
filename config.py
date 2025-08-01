import os
from dotenv import load_dotenv

load_dotenv()

CONFIG = {
    "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
    "JIRA_INSTANCE_URL": os.getenv("JIRA_INSTANCE_URL"),
    "JIRA_USERNAME": os.getenv("JIRA_USERNAME"),
    "JIRA_API_TOKEN": os.getenv("JIRA_API_TOKEN"),
    "JIRA_CLOUD": os.getenv("JIRA_CLOUD", "True").lower() == "true",
    "GRAPH_DB_ENABLED": os.getenv("GRAPH_DB_ENABLED", "True").lower() == "true",
    "NEO4J_URI": os.getenv("NEO4J_URI", "bolt://neo4j:7687"),
    "NEO4J_USERNAME": os.getenv("NEO4J_USERNAME", "neo4j"),
    "NEO4J_PASSWORD": os.getenv("NEO4J_PASSWORD", "test1234"),
    "LANGCHAIN_API_KEY": os.getenv("LANGCHAIN_API_KEY"),
    "LANGCHAIN_PROJECT": os.getenv("LANGCHAIN_PROJECT", "tahecho"),
    "OPENAI_SETTINGS": {
        "model": "gpt-4o",
        "temperature": 0.7,
        "max_tokens": 1000,
        "top_p": 1,
        "frequency_penalty": 0,
        "presence_penalty": 0,
        "stream": False,
    },
}
