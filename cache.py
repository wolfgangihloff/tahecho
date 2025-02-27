import json

jira_issues_cache = None

def fetch_and_cache_jira_issues():
    global jira_issues_cache
    from jira_client import get_all_jira_issues

    jira_issues_cache = get_all_jira_issues()
    print("[CACHE] Issues de Jira actualizadas en la memoria.")

def get_cached_jira_issues():
    if jira_issues_cache:
        return jira_issues_cache
    return "No hay incidencias almacenadas. Intenta recargar los datos de Jira."
