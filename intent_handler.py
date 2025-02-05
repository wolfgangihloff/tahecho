from jira_client import jira_client

async def handle_function_call(response):
    """Processes function calls and executes the required function"""
    if response.choices[0].message.function_call:
        function_name = response.choices[0].message.function_call.name

        if function_name == "get_my_jira_issues":
            return await jira_client.get_my_jira_issues()
    
    return None
