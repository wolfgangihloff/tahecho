from config import CONFIG
from openai import OpenAI

client = OpenAI(api_key=CONFIG["OPENAI_API_KEY"])

def get_openai_response(messages, functions):
    """Calls OpenAI API with function calling enabled"""
    response = client.chat.completions.create(
        messages=messages,
        functions=functions,
        function_call="auto",
        **CONFIG["OPENAI_SETTINGS"]
    )
    return response
