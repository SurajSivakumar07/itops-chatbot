
import os
import requests
import re
import urllib
from requests.auth import HTTPBasicAuth
from src.config.llm import issues_llm as llm

# Getting all the env keys
DOMAIN = os.getenv("JIRA_URL")
EMAIL = os.getenv("JIRA_EMAIL")
API_TOKEN = os.getenv("JIRA_API_TOKEN")
PROJECT_KEY = os.getenv("PROJECT_KEY")

# API URLs
ISSUE_TYPE_URL = f"https://{DOMAIN}/rest/api/3/issuetype"
SEARCH_ISSUES_URL = f"https://{DOMAIN}/rest/api/3/search"
CREATE_ISSUE_URL = f"https://{DOMAIN}/rest/api/3/issue"
KB_ARTICLES_URL = f"https://{DOMAIN}/rest/servicedeskapi/knowledgebase/article"

AUTH = HTTPBasicAuth(EMAIL, API_TOKEN)
HEADERS = {"Accept": "application/json", "Content-Type": "application/json"}


def get_task_issue_type_id():
    """Fetch the correct issue type ID for 'Task'."""
    response = requests.get(ISSUE_TYPE_URL, headers=HEADERS, auth=AUTH)
    if response.status_code == 200:
        for issue_type in response.json():
            if issue_type["name"].lower() == "task":
                return issue_type["id"]
    return None


def extract_issue_details(user_input):
    """Extracts issue details using Gemini AI."""
    prompt = f"""
    Extract Jira issue details:
    Input: "{user_input}"
    Provide output as:
    Summary: <summary>
    Description: <description>
    """
    result = llm.invoke(prompt)
    response_text = result.content
    summary, description = "", ""
    for line in response_text.split('\n'):
        if line.startswith("Summary:"):
            summary = line[len("Summary:"):].strip()
        elif line.startswith("Description:"):
            description = line[len("Description:"):].strip()
    return summary, description


def search_jira_issues(summary):
    """Searches for similar resolved Jira issues."""
    jql_query = f'project = "{PROJECT_KEY}" AND summary ~ "{summary}" AND status = "DONE"'
    encoded_jql = urllib.parse.quote(jql_query)
    response = requests.get(f"{SEARCH_ISSUES_URL}?jql={encoded_jql}", headers=HEADERS, auth=AUTH)
    if response.status_code == 200 and response.json().get("issues"):
        return response.json()["issues"]
    return []


def create_jira_issue(summary, description):
    """Creates a new Jira issue."""
    issue_type_id = get_task_issue_type_id()
    if not issue_type_id:
        return None
    payload = {
        "fields": {
            "project": {"key": PROJECT_KEY},
            "summary": summary,
            "description": {"type": "doc", "version": 1, "content": [{"type": "paragraph", "content": [{"type": "text", "text": description}]}]},
            "issuetype": {"id": str(issue_type_id)}
        }
    }
    response = requests.post(CREATE_ISSUE_URL, json=payload, headers=HEADERS, auth=AUTH)
    return response.json().get("key") if response.status_code == 201 else None


def search_knowledge_base(query):
    """Searches the Jira knowledge base for relevant articles."""
    params = {"serviceDeskId": 1, "query": query, "highlight": "true", "limit": 10}
    response = requests.get(KB_ARTICLES_URL, auth=AUTH, headers=HEADERS, params=params)
    if response.status_code == 200 and response.json().get("values"):
        return response.json()["values"]
    return []


def remove_highlight(text):
    """Removes Atlassian highlight markers."""
    return re.sub(r"@@@hl@@@|@@@endhl@@@", "", text)


def handle_user_issue(user_input):
    summary, description = extract_issue_details(user_input)
    similar_issues = search_jira_issues(summary)
    if similar_issues:
        print("Found similar issues:")
        for issue in similar_issues[:5]:
            print(f"- {issue['key']}: {issue['fields']['summary']}, Status: {issue['fields']['status']['name']}")
        return
    articles = search_knowledge_base(summary)
    if articles:
        print("Found relevant knowledge base articles:")
        for article in articles:
            print(f"🔹 Title: {remove_highlight(article['title'])}")
            print(f"📝 Excerpt: {remove_highlight(article['excerpt'])}")
            print(f"🔗 View Article: {article['content']['iframeSrc']}")
        return
    issue_key = create_jira_issue(summary, description)
    if issue_key:
        print(f"New issue created: {issue_key}")
    else:
        print("Failed to create a new issue.")


# Example usage
if __name__ == "__main__":
    user_query = input("Enter issue details: ")
    handle_user_issue(user_query)

