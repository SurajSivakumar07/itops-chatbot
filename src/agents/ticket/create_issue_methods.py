import os
import urllib
import requests
from src.config.llm import issues_llm as llm
import re
import json
#Getting all the env keys
JIRA_URL = os.getenv("JIRA_URL")
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")
PROJECT_KEY = os.getenv("PROJECT_KEY")
auth = (JIRA_EMAIL, JIRA_API_TOKEN)

def get_task_issue_type_id():
    """Fetch the correct issue type ID for 'Task'."""
    url = f"{JIRA_URL}/rest/api/3/issuetype"

    headers = {"Accept": "application/json"}

    response = requests.get(url, headers=headers, auth=auth)
    if response.status_code == 200:
        issue_types = response.json()
        for issue_type in issue_types:
            if issue_type["name"].lower() == "task":
                print(f"Using Issue Type: {issue_type['name']} (ID: {issue_type['id']})")
                return issue_type["id"]
        print("Error: 'Task' issue type not found.")
    else:
        print(f"Failed to fetch issue types: {response.json()}")
    return None


def extract_issue_details(user_input):
    """Extracts issue details using Gemini AI."""
    print("Extracting Issue Details using Gemini...")
    prompt = f"""
    You are an AI assistant extracting Jira issue details.
    Analyze the input and extract:
    - Summary
    - Description

    Input: "{user_input}"
    Provide the response in the format:
    Summary: <summary>
    Description: <description>
    """
    result = llm.invoke(prompt)
    response_text = result.content


    lines = response_text.split('\n')
    summary = ""
    description = ""
    current_section = None

    for line in lines:
        if line.startswith("Summary:"):
            current_section = "summary"
            summary = line[len("Summary:"):].strip()
        elif line.startswith("Description:"):
            current_section = "description"
            description = line[len("Description:"):].strip()
        elif current_section == "description" and line.strip():
            # Append additional description lines
            description += " " + line.strip()

    return summary, description

def search_jira_issues(summary):
    """
    Searches for similar resolved Jira issues and returns their solution from comments.
    Returns a list of matched issues with key, summary, status, and latest public comment as solution.
    """
    import urllib.parse
    import requests

    print("Searching Jira for Similar Issues...")
    jql_query = f'project = "{PROJECT_KEY}" AND summary ~ "{summary}" AND status = "DONE"'
    encoded_jql = urllib.parse.quote(jql_query)
    url = f"{JIRA_URL}/rest/api/3/search?jql={encoded_jql}&maxResults=5"

    headers = {"Accept": "application/json"}

    response = requests.get(url, headers=headers, auth=auth)
    if response.status_code != 200:
        print(f"Error: {response.status_code}, {response.json()}")
        return False

    issues = response.json().get("issues", [])
    if not issues:
        print("No similar resolved issues found.")
        return False

    results = []

    for issue in issues:
        key = issue["key"]
        fields = issue["fields"]
        summary = fields.get("summary", "No summary")
        status = fields.get("status", {}).get("name", "Unknown")

        # Fetch comments for the issue
        comments_url = f"{JIRA_URL}/rest/api/3/issue/{key}/comment"
        comments_response = requests.get(comments_url, headers=headers, auth=auth)

        if comments_response.status_code == 200:
            comments_data = comments_response.json()
            comments = comments_data.get("comments", [])

            # Get the latest public comment (could be enhanced to use internal notes too)
            if comments:
                latest_comment = comments[-1]  # or use comments[0] for oldest
                solution = latest_comment.get("body", {}).get("content", [{}])[0].get("content", [{}])[0].get("text",
                                                                                                              "No solution text")
            else:
                solution = "No comments found"
        else:
            solution = f"Failed to retrieve comments ({comments_response.status_code})"

        print(f"- {key}: {summary}, Status: {status}")
        print(f"  ➤ Solution: {solution[:200]}{'...' if len(solution) > 200 else ''}")

        results.append({
            "key": key,
            "summary": summary,
            "status": status,
            "solution": solution
        })

    return results


def create_jira_issue(summary, description):
    """Creates a new Jira issue with the correct Task issue type."""
    issue_type_id = get_task_issue_type_id()
    if not issue_type_id:
        print("Cannot create issue without a valid Task issue type.")
        return

    print("Creating a New Jira Issue...")
    url = f"{JIRA_URL}/rest/api/3/issue"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }


    # Convert description to Atlassian Document Format (ADF)
    adf_description = {
        "type": "doc",
        "version": 1,
        "content": [
            {"type": "paragraph", "content": [{"type": "text", "text": description}]}
        ]
    }

    payload = {
        "fields": {
            "project": {"key": PROJECT_KEY},
            "summary": summary,
            "description": adf_description,
            "issuetype": {"id": str(issue_type_id)}
        }
    }

    response = requests.post(url, json=payload, headers=headers, auth=auth)
    if response.status_code == 201:
        print(f"Issue created successfully! Issue Key: {response.json()['key']}")
        return {"ticket_Key":response.json()['key'],"ticket_id":response.json()['id']}
    else:
        print(f"Failed to create issue: {response.json()}")
        return None



#Removing highlights
def remove_highlight(text):
    """Removes Atlassian highlight markers (@@@hl@@@ and @@@endhl@@@)"""
    return re.sub(r"@@@hl@@@|@@@endhl@@@", "", text)


#function to call the knowledge article


def serach_knowledge_article(summary):
    URL = f"{JIRA_URL}/rest/servicedeskapi/knowledgebase/article"
    PARAMS = {
        "serviceDeskId": 1,
        "query": summary,
        "highlight": "true",
        "limit": 10
    }
    HEADERS = {"Accept": "application/json"}

    response = requests.get(URL, auth=auth, headers=HEADERS, params=PARAMS)
    if response.status_code == 200:
        data = response.json()

        # Check if articles are found
        if not data.get("values"):
            print("No articles found for the given query.")
        else:
            print("\n📚 Knowledge Base Articles:\n")
            for article in data["values"]:
                title = remove_highlight(article["title"])
                excerpt = remove_highlight(article["excerpt"])
                view_link = article["content"]["iframeSrc"]

                print(f"🔹 Title: {title}")
                print(f"📝 Excerpt: {excerpt}")
                print(f"🔗 View Article: {view_link}")
                print("-" * 80)

                return {"title": title, "excerpt": excerpt, "view_link": view_link}

    else:
        print(f"❌ Error {response.status_code}: {response.text}")

