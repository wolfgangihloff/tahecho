import os
from dotenv import load_dotenv

load_dotenv()

CONFIG = {
    "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
    "JIRA_INSTANCE_URL": os.getenv("JIRA_INSTANCE_URL"),
    "JIRA_USERNAME": os.getenv("JIRA_USERNAME"),
    "JIRA_API_TOKEN": os.getenv("JIRA_API_TOKEN"),
    "JIRA_CLOUD": os.getenv("JIRA_CLOUD", "True").lower() == "true",
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
